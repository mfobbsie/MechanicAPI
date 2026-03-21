# app/seed_admin.py

from app.models import db, Customer, Role
from werkzeug.security import generate_password_hash

def seed_admin():
    # Ensure the admin role exists
    admin_role = db.session.execute(
        db.select(Role).where(Role.role_name == "admin")
    ).scalar_one_or_none()

    if not admin_role:
        admin_role = Role(role_name="admin")
        db.session.add(admin_role)
        db.session.commit()
        print("Created admin role.")

    # Ensure the admin user exists
    admin_user = db.session.execute(
        db.select(Customer).where(Customer.email == "admin@example.com")
    ).scalar_one_or_none()

    if not admin_user:
        admin_user = Customer(
            name="Admin",
            email="admin@example.com",
            password=generate_password_hash("1234"),
            role_id=admin_role.id
        )
        db.session.add(admin_user)
        db.session.commit()
        print("Created admin user: admin@example.com / 1234")
    else:
        print("Admin user already exists.")
