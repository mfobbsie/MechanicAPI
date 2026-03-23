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
    Inventory,
)


class TestInventory(unittest.TestCase):

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
                role_id=admin_role.id,
            )
            db.session.add(admin)

            # Seed a regular customer (for tickets)
            customer = Customer(
                name="Ticket Customer",
                email="customer@example.com",
                phone="555-1111",
                password=generate_password_hash("1234", method="pbkdf2:sha256"),
                role_id=customer_role.id,
            )
            db.session.add(customer)
            db.session.commit()

            # Seed mechanic (salary required)
            mech = Mechanic(
                name="Mike Mechanic",
                email="mech@example.com",
                phone="555-2222",
                password=generate_password_hash("1234", method="pbkdf2:sha256"),
                salary=60000,
                role_id=admin_role.id,
            )
            db.session.add(mech)
            db.session.commit()

            # Seed a service ticket for add_part tests
            ticket = Service_Tickets(
                VIN="INVTESTVIN",
                service_date=date.today(),
                description="Test ticket for inventory",
                customer_id=customer.id,
            )
            db.session.add(ticket)
            db.session.commit()
            self.ticket_id = ticket.id

        self.client = self.app.test_client()

        # Login admin (not strictly required for these routes, but consistent with your pattern)
        login_res = self.client.post("/customers/login", json={
            "email": "admin@example.com",
            "password": "1234"
        })
        self.token = login_res.json["auth_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    # ---------------------------------------------------------
    # CREATE INVENTORY ITEM
    # ---------------------------------------------------------
    def test_create_inventory_item(self):
        payload = {
            "item_name": "Oil Filter",
            "quantity": 10,
            "price": 19.99
        }

        res = self.client.post("/inventory", json=payload)
        self.assertEqual(res.status_code, 201)
        self.assertIn("id", res.json)
        self.assertEqual(res.json["item_name"], "Oil Filter")

    # ---------------------------------------------------------
    # GET ALL INVENTORY ITEMS
    # ---------------------------------------------------------
    def test_get_inventory(self):
        # Seed one item
        self.client.post("/inventory", json={
            "item_name": "Brake Pads",
            "quantity": 5,
            "price": 49.99
        })

        res = self.client.get("/inventory")
        self.assertEqual(res.status_code, 200)
        self.assertIn("inventory", res.json)
        self.assertGreaterEqual(len(res.json["inventory"]), 1)

    # ---------------------------------------------------------
    # GET SINGLE INVENTORY ITEM
    # ---------------------------------------------------------
    def test_get_inventory_item(self):
        create_res = self.client.post("/inventory", json={
            "item_name": "Air Filter",
            "quantity": 3,
            "price": 15.50
        })
        item_id = create_res.json["id"]

        res = self.client.get(f"/inventory/{item_id}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json["id"], item_id)

    def test_get_inventory_item_not_found(self):
        res = self.client.get("/inventory/999")
        self.assertEqual(res.status_code, 404)
        self.assertIn("message", res.json)

    # ---------------------------------------------------------
    # UPDATE INVENTORY ITEM
    # ---------------------------------------------------------
    def test_update_inventory_item(self):
        create_res = self.client.post("/inventory", json={
            "item_name": "Coolant",
            "quantity": 8,
            "price": 25.00
        })
        item_id = create_res.json["id"]

        update_res = self.client.put(f"/inventory/{item_id}", json={
            "quantity": 12,
            "price": 27.50
        })

        self.assertEqual(update_res.status_code, 200)
        self.assertEqual(update_res.json["quantity"], 12)
        self.assertEqual(update_res.json["price"], 27.50)

    def test_update_inventory_item_not_found(self):
        res = self.client.put("/inventory/999", json={
            "quantity": 10
        })
        self.assertEqual(res.status_code, 404)
        self.assertIn("message", res.json)

    # ---------------------------------------------------------
    # DELETE INVENTORY ITEM
    # ---------------------------------------------------------
    def test_delete_inventory_item(self):
        create_res = self.client.post("/inventory", json={
            "item_name": "Spark Plug",
            "quantity": 20,
            "price": 5.99
        })
        item_id = create_res.json["id"]

        delete_res = self.client.delete(f"/inventory/{item_id}")
        self.assertEqual(delete_res.status_code, 200)
        self.assertIn("message", delete_res.json)

        # Confirm it's gone
        get_res = self.client.get(f"/inventory/{item_id}")
        self.assertEqual(get_res.status_code, 404)

    def test_delete_inventory_item_not_found(self):
        res = self.client.delete("/inventory/999")
        self.assertEqual(res.status_code, 404)
        self.assertIn("message", res.json)

    # ---------------------------------------------------------
    # ADD PART TO SERVICE TICKET
    # ---------------------------------------------------------
    def test_add_part_to_ticket(self):
        # Create inventory item
        create_item = self.client.post("/inventory", json={
            "item_name": "Timing Belt",
            "quantity": 5,
            "price": 120.00
        })
        inventory_id = create_item.json["id"]

        res = self.client.post(
            f"/service_tickets/{self.ticket_id}/add_part",
            json={
                "inventory_id": inventory_id,
                "quantity_used": 2
            }
        )

        self.assertEqual(res.status_code, 201)
        self.assertIn("message", res.json)

        # Confirm quantity reduced
        get_item = self.client.get(f"/inventory/{inventory_id}")
        self.assertEqual(get_item.json["quantity"], 3)

    def test_add_part_ticket_not_found(self):
        # Create inventory item
        create_item = self.client.post("/inventory", json={
            "item_name": "Alternator",
            "quantity": 2,
            "price": 250.00
        })
        inventory_id = create_item.json["id"]

        res = self.client.post(
            "/service_tickets/999/add_part",
            json={
                "inventory_id": inventory_id,
                "quantity_used": 1
            }
        )

        self.assertEqual(res.status_code, 404)
        self.assertIn("message", res.json)

    def test_add_part_inventory_not_found(self):
        res = self.client.post(
            f"/service_tickets/{self.ticket_id}/add_part",
            json={
                "inventory_id": 999,
                "quantity_used": 1
            }
        )

        self.assertEqual(res.status_code, 404)
        self.assertIn("message", res.json)

    def test_add_part_not_enough_stock(self):
        # Create inventory item with low stock
        create_item = self.client.post("/inventory", json={
            "item_name": "Headlight",
            "quantity": 1,
            "price": 80.00
        })
        inventory_id = create_item.json["id"]

        res = self.client.post(
            f"/service_tickets/{self.ticket_id}/add_part",
            json={
                "inventory_id": inventory_id,
                "quantity_used": 5
            }
        )

        self.assertEqual(res.status_code, 400)
        self.assertIn("message", res.json)
