# app/cli.py

import click
from werkzeug.security import generate_password_hash
from app.models import db, Customer, Role


def register_cli(app):
    @app.cli.command("seed-admin")
    def seed_admin():
        """Seed the admin role and user."""
        with app.app_context():
            # Ensure the admin role exists
            admin_role = Role.query.filter_by(role_name="admin").first()
            if not admin_role:
                admin_role = Role(role_name="admin")
                db.session.add(admin_role)
                db.session.commit()
                click.echo("Created admin role.")

            # Ensure the admin user exists
            admin_user = Customer.query.filter_by(email="admin@example.com").first()
            if not admin_user:
                admin_user = Customer(
                    name="Admin",
                    phone="000-000-0000",
                    email="admin@example.com",
                    password=generate_password_hash("1234"),
                    role_id=admin_role.id,
                )
                db.session.add(admin_user)
                db.session.commit()
                click.echo("Created admin user: admin@example.com / 1234")
            else:
                click.echo("Admin user already exists.")

