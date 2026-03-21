# migrations/env.py

from __future__ import with_statement

from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool

from app.models import Base  # SQLAlchemy 2.0 Declarative Base
from app import create_app


# -----------------------------
# Load Flask app + config
# -----------------------------
app = create_app()
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# -----------------------------
# Set target metadata
# -----------------------------
target_metadata = Base.metadata


# -----------------------------
# Run migrations offline
# -----------------------------
def run_migrations_offline():
    """Run migrations without a DB connection."""
    url = app.config["SQLALCHEMY_DATABASE_URI"]
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# -----------------------------
# Run migrations online
# -----------------------------
def run_migrations_online():
    """Run migrations with a DB connection."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = app.config["SQLALCHEMY_DATABASE_URI"]

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,        # detect column type changes
            compare_server_default=True,
            compare_nullable=True,
        )

        with context.begin_transaction():
            context.run_migrations()


# -----------------------------
# Entrypoint
# -----------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
