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