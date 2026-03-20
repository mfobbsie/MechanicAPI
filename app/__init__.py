from flask import Flask
from .extensions import ma, limiter, cache
from app.models import db, Customer, Service_Tickets, Mechanic
from app.config import DevelopmentConfig, TestingConfig, ProductionConfig
from .blueprints.customers import customers_bp
from .blueprints.service_tickets import service_tickets_bp
from .blueprints.mechanics import mechanics_bp

def create_app(config_name):
    app = Flask(__name__)
    
    app.config.from_object(f'app.config.{config_name}')
    
    
    #initalize extensions
    ma.init_app(app)
    db.init_app(app)
    limiter.init_app(app)
    cache.init_app(app)
    
    #Register blueprints
    app.register_blueprint(customers_bp, url_prefix='/customers')
    app.register_blueprint(service_tickets_bp, url_prefix='/service_tickets')
    app.register_blueprint(mechanics_bp, url_prefix='/mechanics')
    
    return app