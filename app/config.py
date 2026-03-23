# app/config.py

import os


class Config:
    # -----------------------------------------
    # Database Configuration
    # -----------------------------------------
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get(
            "DATABASE_URL",
            "mysql+mysqlconnector://root:ellietteGrace22@localhost/mechanic_db"
        )
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False  # prevents overhead + warnings

    # -----------------------------------------
    # Debugging
    # -----------------------------------------
    DEBUG = True

    # -----------------------------------------
    # Caching
    # -----------------------------------------
    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 300

    # -----------------------------------------
    # Security (JWT, etc.)
    # -----------------------------------------
    SECRET_KEY = os.environ.get("SECRET_KEY", "a super secret, secret key")


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///testing.db'
    TESTING = True
    DEBUG = False
    CACHE_TYPE = 'SimpleCache'


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "mysql+mysqlconnector://root:ellietteGrace22@localhost/mechanic_db")