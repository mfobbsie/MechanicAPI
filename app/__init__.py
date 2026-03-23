# app/__init__.py

from flask import Flask
from app.models import db
from app.extensions import ma, limiter, cache, migrate
from app.blueprints.customers import customers_bp
from app.blueprints.mechanics import mechanics_bp
from app.blueprints.service_tickets import service_tickets_bp
from app.blueprints.inventory import inventory_bp
from app.cli import register_cli
from flask_swagger_ui import get_swaggerui_blueprint

def create_app(config_name="Config"):
    # Swagger UI
    SWAGGER_URL = '/api/docs'
    API_URL = '/static/swagger.yaml'
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={'app_name': "Mechanics API"}
    )

    app = Flask(__name__)

    # ⭐ Load config dynamically
    app.config.from_object(f"app.config.{config_name}")

    # Initialize extensions
    db.init_app(app)
    ma.init_app(app)
    limiter.init_app(app)
    cache.init_app(app)
    migrate.init_app(app, db)

    # Import models AFTER db.init_app
    from app.models import (
        Customer,
        Mechanic,
        Service_Tickets,
        Inventory,
        Inventory_Service_Ticket,
        Role
    )

    # Create tables
    with app.app_context():
        db.create_all()

    # Register CLI commands
    register_cli(app)

    # Register blueprints
    app.register_blueprint(customers_bp, url_prefix="/customers")
    app.register_blueprint(mechanics_bp, url_prefix="/mechanics")
    app.register_blueprint(service_tickets_bp, url_prefix="/service_tickets")
    app.register_blueprint(inventory_bp, url_prefix="/inventory")
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    return app
