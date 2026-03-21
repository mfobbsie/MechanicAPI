# app/extensions.py

from flask_marshmallow import Marshmallow
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from flask_migrate import Migrate


# -----------------------------
# Marshmallow (serialization)
# -----------------------------
ma = Marshmallow()


# -----------------------------
# Rate Limiter
# -----------------------------

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["300 per minute"],
    storage_uri="memory://"
)


# -----------------------------
# Cache
# -----------------------------
cache = Cache(config={"CACHE_TYPE": "SimpleCache"})


# -----------------------------
# Database Migrations
# -----------------------------
migrate = Migrate()
