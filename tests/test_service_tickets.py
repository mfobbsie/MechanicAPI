import unittest
from datetime import date
from werkzeug.security import generate_password_hash
from app import create_app
from app.models import db, Role, Customer, Mechanic, Service_Tickets


class TestServiceTickets(unittest.TestCase):

    def setUp(self):
        self.app = create_app("TestingConfig")

        with self.app.app_context():
            db.drop_all()
            db.create_all()

            # Seed roles
            admin_role = Role(role_name="admin")
            customer_role = Role(role_name="customer")
            db.session.add_all([admin_role, customer_role])
            db.session.commit()

            # Seed admin user
            admin = Customer(
                name="Admin User",
                email="admin@example.com",
                phone="555-0000",
                password=generate_password_hash("1234", method="pbkdf2:sha256"),
                role_id=admin_role.id
            )
            db.session.add(admin)
            db.session.commit()

            # Seed a mechanic
            mech = Mechanic(
                name="Mike Mechanic",
                email="mech@example.com",
                phone="555-2222",
                password=generate_password_hash("1234", method="pbkdf2:sha256"),
                salary=60000,
                role_id=admin_role.id  # mechanics use admin role in your schema
            )
            db.session.add(mech)
            db.session.commit()

        self.client = self.app.test_client()

        # Login admin to get token
        login_res = self.client.post("/customers/login", json={
            "email": "admin@example.com",
            "password": "1234"
        })
        self.token = login_res.json["auth_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    # ---------------------------------------------------------
    # CREATE SERVICE TICKET
    # ---------------------------------------------------------
    def test_create_service_ticket(self):
        payload = {
            "VIN": "VIN123",
            "service_date": str(date.today()),
            "description": "Oil change",
            "customer_id": 1
        }

        res = self.client.post("/service_tickets", json=payload)
        self.assertEqual(res.status_code, 201)
        self.assertIn("id", res.json)

    def test_create_ticket_duplicate(self):
        payload = {
            "VIN": "VIN123",
            "service_date": str(date.today()),
            "description": "Oil change",
            "customer_id": 1
        }

        self.client.post("/service_tickets", json=payload)
        res = self.client.post("/service_tickets", json=payload)

        self.assertEqual(res.status_code, 400)
        self.assertIn("message", res.json)

    # ---------------------------------------------------------
    # GET ALL TICKETS
    # ---------------------------------------------------------
    def test_get_all_tickets(self):
        res = self.client.get("/service_tickets")
        self.assertEqual(res.status_code, 200)
        self.assertIn("service_tickets", res.json)

    # ---------------------------------------------------------
    # GET TICKET BY ID
    # ---------------------------------------------------------
    def test_get_ticket_by_id(self):
        payload = {
            "VIN": "VIN999",
            "service_date": str(date.today()),
            "description": "Brake job",
            "customer_id": 1
        }
        create_res = self.client.post("/service_tickets", json=payload)
        ticket_id = create_res.json["id"]

        res = self.client.get(f"/service_tickets/{ticket_id}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json["id"], ticket_id)

    def test_get_ticket_not_found(self):
        res = self.client.get("/service_tickets/999")
        self.assertEqual(res.status_code, 404)

    # ---------------------------------------------------------
    # UPDATE TICKET
    # ---------------------------------------------------------
    def test_update_ticket(self):
        payload = {
            "VIN": "VIN111",
            "service_date": str(date.today()),
            "description": "Tune up",
            "customer_id": 1
        }
        create_res = self.client.post("/service_tickets", json=payload)
        ticket_id = create_res.json["id"]

        update_res = self.client.put(
            f"/service_tickets/{ticket_id}/update",
            json={"description": "Updated description"}
        )

        self.assertEqual(update_res.status_code, 200)
        self.assertEqual(update_res.json["description"], "Updated description")

    def test_update_ticket_duplicate_vin_date(self):
        # Create ticket 1
        t1 = {
            "VIN": "VIN-A",
            "service_date": str(date.today()),
            "description": "Job A",
            "customer_id": 1
        }
        self.client.post("/service_tickets", json=t1)

        # Create ticket 2
        t2 = {
            "VIN": "VIN-B",
            "service_date": str(date.today()),
            "description": "Job B",
            "customer_id": 1
        }
        create_res = self.client.post("/service_tickets", json=t2)
        ticket2_id = create_res.json["id"]

        # Attempt to update ticket2 to match ticket1's VIN + date
        update_res = self.client.put(
            f"/service_tickets/{ticket2_id}/update",
            json={"VIN": "VIN-A"}
        )

        self.assertEqual(update_res.status_code, 400)

    # ---------------------------------------------------------
    # ASSIGN MECHANIC
    # ---------------------------------------------------------
    def test_assign_mechanic(self):
        # Create ticket
        payload = {
            "VIN": "VIN777",
            "service_date": str(date.today()),
            "description": "Engine check",
            "customer_id": 1
        }
        create_res = self.client.post("/service_tickets", json=payload)
        ticket_id = create_res.json["id"]

        res = self.client.post(f"/service_tickets/{ticket_id}/assign_mechanic/1")
        self.assertEqual(res.status_code, 200)

    def test_assign_mechanic_already_assigned(self):
        payload = {
            "VIN": "VIN888",
            "service_date": str(date.today()),
            "description": "Alignment",
            "customer_id": 1
        }
        create_res = self.client.post("/service_tickets", json=payload)
        ticket_id = create_res.json["id"]

        # Assign once
        self.client.post(f"/service_tickets/{ticket_id}/assign_mechanic/1")

        # Assign again
        res = self.client.post(f"/service_tickets/{ticket_id}/assign_mechanic/1")
        self.assertEqual(res.status_code, 400)

    def test_assign_mechanic_ticket_not_found(self):
        res = self.client.post("/service_tickets/999/assign_mechanic/1")
        self.assertEqual(res.status_code, 404)

    def test_assign_mechanic_not_found(self):
        # Create ticket
        payload = {
            "VIN": "VIN9999",
            "service_date": str(date.today()),
            "description": "Inspection",
            "customer_id": 1
        }
        create_res = self.client.post("/service_tickets", json=payload)
        ticket_id = create_res.json["id"]

        res = self.client.post(f"/service_tickets/{ticket_id}/assign_mechanic/999")
        self.assertEqual(res.status_code, 404)

    # ---------------------------------------------------------
    # REMOVE MECHANIC
    # ---------------------------------------------------------
    def test_remove_mechanic(self):
        payload = {
            "VIN": "VIN555",
            "service_date": str(date.today()),
            "description": "Cooling system",
            "customer_id": 1
        }
        create_res = self.client.post("/service_tickets", json=payload)
        ticket_id = create_res.json["id"]

        # Assign
        self.client.post(f"/service_tickets/{ticket_id}/assign_mechanic/1")

        # Remove
        res = self.client.put(f"/service_tickets/{ticket_id}/remove_mechanic/1")
        self.assertEqual(res.status_code, 200)

    def test_remove_mechanic_not_assigned(self):
        payload = {
            "VIN": "VIN666",
            "service_date": str(date.today()),
            "description": "Battery",
            "customer_id": 1
        }
        create_res = self.client.post("/service_tickets", json=payload)
        ticket_id = create_res.json["id"]

        res = self.client.put(f"/service_tickets/{ticket_id}/remove_mechanic/1")
        self.assertEqual(res.status_code, 400)

    def test_remove_mechanic_ticket_not_found(self):
        res = self.client.put("/service_tickets/999/remove_mechanic/1")
        self.assertEqual(res.status_code, 404)

    def test_remove_mechanic_not_found(self):
        payload = {
            "VIN": "VIN7777",
            "service_date": str(date.today()),
            "description": "Diagnostics",
            "customer_id": 1
        }
        create_res = self.client.post("/service_tickets", json=payload)
        ticket_id = create_res.json["id"]

        res = self.client.put(f"/service_tickets/{ticket_id}/remove_mechanic/999")
        self.assertEqual(res.status_code, 404)
