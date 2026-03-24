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
    SWAGGER_URL = '/api/docs'
    API_URL = '/static/swagger.yaml'
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={'app_name': "Mechanics API"}
    )

    import os
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    STATIC_DIR = os.path.join(BASE_DIR, "..", "static")

    app = Flask(
        __name__, 
        static_folder=STATIC_DIR,
        static_url_path='/static')
    app.config.from_object(f"app.config.{config_name}")

    # Initialize extensions
    db.init_app(app)
    ma.init_app(app)
    limiter.init_app(app)
    cache.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    app.register_blueprint(customers_bp, url_prefix="/customers")
    app.register_blueprint(mechanics_bp, url_prefix="/mechanics")
    app.register_blueprint(service_tickets_bp, url_prefix="/service_tickets")
    app.register_blueprint(inventory_bp, url_prefix="/inventory")
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    # ⭐ Exempt all Swagger UI routes
    for rule in app.url_map.iter_rules():
        if rule.rule.startswith("/api/docs"):
            limiter.exempt(app.view_functions[rule.endpoint])

    return app