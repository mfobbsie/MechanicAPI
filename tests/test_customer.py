import unittest
from app import create_app
from app.models import db, Role, Customer, Service_Tickets
from werkzeug.security import generate_password_hash
from datetime import date


class TestCustomer(unittest.TestCase):

    def setUp(self):
        self.app = create_app("TestingConfig")

        with self.app.app_context():
            db.drop_all()
            db.create_all()

            # Seed roles
            customer_role = Role(role_name="customer")
            admin_role = Role(role_name="admin")
            db.session.add_all([customer_role, admin_role])
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

        self.client = self.app.test_client()

    # ---------------------------------------------------------
    # CREATE CUSTOMER
    # ---------------------------------------------------------
    def test_create_customer(self):
        payload = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "555-1234",
            "password": "1234"
        }

        response = self.client.post("/customers", json=payload)
        self.assertEqual(response.status_code, 201)
        self.assertIn("id", response.json)

    def test_create_customer_missing_email(self):
        payload = {
            "name": "Jane Doe",
            "phone": "555-5678",
            "password": "1234"
        }

        response = self.client.post("/customers", json=payload)
        self.assertEqual(response.status_code, 400)

    # ---------------------------------------------------------
    # LOGIN
    # ---------------------------------------------------------
    def test_login_admin(self):
        payload = {
            "email": "admin@example.com",
            "password": "1234"
        }

        response = self.client.post("/customers/login", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn("auth_token", response.json)

    def test_login_wrong_password(self):
        payload = {
            "email": "admin@example.com",
            "password": "wrong"
        }

        response = self.client.post("/customers/login", json=payload)
        self.assertEqual(response.status_code, 401)

    def test_login_missing_fields(self):
        response = self.client.post("/customers/login", json={})
        self.assertEqual(response.status_code, 400)

    # ---------------------------------------------------------
    # GET ALL CUSTOMERS
    # ---------------------------------------------------------
    def test_get_all_customers(self):
        response = self.client.get("/customers")
        self.assertEqual(response.status_code, 200)
        self.assertIn("customers", response.json)

    # ---------------------------------------------------------
    # GET MY TICKETS
    # ---------------------------------------------------------
    def test_get_my_tickets(self):
        # Create a customer
        payload = {
            "name": "Ticket User",
            "email": "ticket@example.com",
            "phone": "555-7777",
            "password": "1234"
        }
        create_res = self.client.post("/customers", json=payload)
        customer_id = create_res.json["id"]

        # Login to get token
        login_res = self.client.post("/customers/login", json={
            "email": "ticket@example.com",
            "password": "1234"
        })
        token = login_res.json["auth_token"]

        # Create a ticket manually in DB
        with self.app.app_context():
            ticket = Service_Tickets(
                VIN="123VIN",
                service_date=date.today(),
                description="Oil change",
                customer_id=customer_id
            )
            db.session.add(ticket)
            db.session.commit()

        # Call endpoint
        response = self.client.get(
            "/customers/my-tickets",
            headers={"Authorization": f"Bearer {token}"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["customer_id"], customer_id)
        self.assertEqual(len(response.json["tickets"]), 1)

    def test_get_my_tickets_wrong_role(self):
        # Login as admin
        login_res = self.client.post("/customers/login", json={
            "email": "admin@example.com",
            "password": "1234"
        })
        token = login_res.json["auth_token"]

        response = self.client.get(
            "/customers/my-tickets",
            headers={"Authorization": f"Bearer {token}"}
        )

        self.assertEqual(response.status_code, 403)

    # ---------------------------------------------------------
    # UPDATE CUSTOMER
    # ---------------------------------------------------------
    def test_update_customer_self(self):
        # Create customer
        payload = {
            "name": "Update User",
            "email": "update@example.com",
            "phone": "555-8888",
            "password": "1234"
        }
        create_res = self.client.post("/customers", json=payload)
        customer_id = create_res.json["id"]

        # Login
        login_res = self.client.post("/customers/login", json={
            "email": "update@example.com",
            "password": "1234"
        })
        token = login_res.json["auth_token"]

        # Update
        response = self.client.put(
            f"/customers/{customer_id}",
            json={"phone": "555-9999"},
            headers={"Authorization": f"Bearer {token}"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["phone"], "555-9999")

    def test_update_customer_unauthorized(self):
        # Login as admin
        login_res = self.client.post("/customers/login", json={
            "email": "admin@example.com",
            "password": "1234"
        })
        token = login_res.json["auth_token"]

        # Try updating non-existent customer
        response = self.client.put(
            "/customers/999",
            json={"phone": "555-0000"},
            headers={"Authorization": f"Bearer {token}"}
        )

        self.assertEqual(response.status_code, 404)

    # ---------------------------------------------------------
    # DELETE CUSTOMER
    # ---------------------------------------------------------
    def test_delete_customer_self(self):
        # Create customer
        payload = {
            "name": "Delete User",
            "email": "delete@example.com",
            "phone": "555-4444",
            "password": "1234"
        }
        create_res = self.client.post("/customers", json=payload)
        customer_id = create_res.json["id"]

        # Login
        login_res = self.client.post("/customers/login", json={
            "email": "delete@example.com",
            "password": "1234"
        })
        token = login_res.json["auth_token"]

        # Delete
        response = self.client.delete(
            f"/customers/{customer_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        self.assertEqual(response.status_code, 200)

    def test_delete_customer_with_tickets(self):
        # Create customer
        payload = {
            "name": "TicketDelete",
            "email": "td@example.com",
            "phone": "555-2222",
            "password": "1234"
        }
        create_res = self.client.post("/customers", json=payload)
        customer_id = create_res.json["id"]

        # Login
        login_res = self.client.post("/customers/login", json={
            "email": "td@example.com",
            "password": "1234"
        })
        token = login_res.json["auth_token"]

        # Add ticket
        with self.app.app_context():
            ticket = Service_Tickets(
                VIN="VIN999",
                service_date=date.today(),
                description="Brake job",
                customer_id=customer_id
            )
            db.session.add(ticket)
            db.session.commit()

        # Attempt delete
        response = self.client.delete(
            f"/customers/{customer_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        self.assertEqual(response.status_code, 400)

