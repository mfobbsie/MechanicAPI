import unittest
from datetime import date
from werkzeug.security import generate_password_hash

from app import create_app
from app.models import (
    db,
    Role,
    Customer,
    Mechanic,
    Service_Tickets,
)


class TestMechanics(unittest.TestCase):

    def setUp(self):
        self.app = create_app("TestingConfig")

        with self.app.app_context():
            db.drop_all()
            db.create_all()

            # Seed roles
            admin_role = Role(role_name="admin")
            mechanic_role = Role(role_name="mechanic")
            customer_role = Role(role_name="customer")
            db.session.add_all([admin_role, mechanic_role, customer_role])
            db.session.commit()

            # Seed admin user
            admin = Customer(
                name="Admin User",
                email="admin@example.com",
                phone="555-0000",
                password=generate_password_hash("1234", method="pbkdf2:sha256"),
                role_id=admin_role.id,
            )
            db.session.add(admin)
            db.session.commit()

            # Seed mechanic
            mech = Mechanic(
                name="Mike Mechanic",
                email="mech@example.com",
                phone="555-2222",
                password=generate_password_hash("1234", method="pbkdf2:sha256"),
                salary=60000,
                role_id=mechanic_role.id,
            )
            db.session.add(mech)
            db.session.commit()
            self.mechanic_id = mech.id

            # Seed a service ticket for mechanic ticket tests
            ticket = Service_Tickets(
                VIN="MECHVIN123",
                service_date=date.today(),
                description="Engine diagnostics",
                customer_id=admin.id,
            )
            db.session.add(ticket)
            db.session.commit()

            # Assign mechanic to ticket
            mech.service_tickets.append(ticket)
            db.session.commit()

        self.client = self.app.test_client()

        # Login admin
        login_res = self.client.post("/customers/login", json={
            "email": "admin@example.com",
            "password": "1234"
        })
        self.admin_token = login_res.json["auth_token"]
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}

        # Login mechanic
        mech_login = self.client.post("/mechanics/login", json={
            "email": "mech@example.com",
            "password": "1234"
        })
        self.mech_token = mech_login.json["auth_token"]
        self.mech_headers = {"Authorization": f"Bearer {self.mech_token}"}

    # ---------------------------------------------------------
    # LOGIN
    # ---------------------------------------------------------
    def test_mechanic_login(self):
        res = self.client.post("/mechanics/login", json={
            "email": "mech@example.com",
            "password": "1234"
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn("auth_token", res.json)

    def test_mechanic_login_invalid(self):
        res = self.client.post("/mechanics/login", json={
            "email": "mech@example.com",
            "password": "wrong"
        })
        self.assertEqual(res.status_code, 401)

    # ---------------------------------------------------------
    # CREATE MECHANIC (ADMIN ONLY)
    # ---------------------------------------------------------
    def test_create_mechanic_admin(self):
        payload = {
            "name": "New Mechanic",
            "email": "newmech@example.com",
            "phone": "555-3333",
"password": "abcd",
            "salary": 55000
        }

        res = self.client.post("/mechanics", json=payload, headers=self.admin_headers)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json["email"], "newmech@example.com")

    def test_create_mechanic_unauthorized(self):
        payload = {
            "name": "Bad Mechanic",
            "email": "bad@example.com",
            "phone": "555-4444",
            "password": "abcd",
            "salary": 50000
        }

        res = self.client.post("/mechanics", json=payload, headers=self.mech_headers)
        self.assertEqual(res.status_code, 403)

    # ---------------------------------------------------------
    # GET ALL MECHANICS
    # ---------------------------------------------------------
    def test_get_mechanics(self):
        res = self.client.get("/mechanics")
        self.assertEqual(res.status_code, 200)
        self.assertIn("mechanics", res.json)

    # ---------------------------------------------------------
    # GET MECHANIC BY ID
    # ---------------------------------------------------------
    def test_get_mechanic_by_id(self):
        res = self.client.get(f"/mechanics/{self.mechanic_id}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json["id"], self.mechanic_id)

    def test_get_mechanic_not_found(self):
        res = self.client.get("/mechanics/999")
        self.assertEqual(res.status_code, 404)

    # ---------------------------------------------------------
    # GET MECHANIC SERVICE TICKETS
    # ---------------------------------------------------------
    def test_get_mechanic_service_tickets_admin(self):
        res = self.client.get(
            f"/mechanics/{self.mechanic_id}/service_tickets",
            headers=self.admin_headers
        )
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json, list)

    # ---------------------------------------------------------
    # POPULAR MECHANICS (ADMIN ONLY)
    # ---------------------------------------------------------
    def test_popular_mechanics_admin(self):
        res = self.client.get("/mechanics/popular", headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json, list)

    def test_popular_mechanics_unauthorized(self):
        res = self.client.get("/mechanics/popular", headers=self.mech_headers)
        self.assertEqual(res.status_code, 403)

    # ---------------------------------------------------------
    # UPDATE MECHANIC
    # ---------------------------------------------------------
    def test_update_mechanic_admin(self):
        payload = {
            "id": self.mechanic_id,
            "name": "Updated Mechanic"
        }

        res = self.client.put("/mechanics", json=payload, headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json["name"], "Updated Mechanic")

    def test_update_mechanic_self(self):
        payload = {"name": "Self Updated"}

        res = self.client.put("/mechanics", json=payload, headers=self.mech_headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json["name"], "Self Updated")

    def test_update_mechanic_missing_id_admin(self):
        res = self.client.put("/mechanics", json={}, headers=self.admin_headers)
        self.assertEqual(res.status_code, 400)

    # ---------------------------------------------------------
    # DELETE MECHANIC (ADMIN ONLY)
    # ---------------------------------------------------------
    def test_delete_mechanic_admin(self):
        res = self.client.delete(f"/mechanics/{self.mechanic_id}", headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)

    def test_delete_mechanic_unauthorized(self):
        res = self.client.delete(f"/mechanics/{self.mechanic_id}", headers=self.mech_headers)
        self.assertEqual(res.status_code, 403)

    def test_delete_mechanic_not_found(self):
        res = self.client.delete("/mechanics/999", headers=self.admin_headers)
        self.assertEqual(res.status_code, 404)