# app/utils/util.py

from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError, ExpiredSignatureError
from functools import wraps
from flask import request, jsonify

SECRET_KEY = "a super secret, secret key"


# -----------------------------
# ENCODE TOKEN
# -----------------------------
def encode_token(user_id, role):
    
    payload = {
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
        "sub": str(user_id),
        "role": role
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token


# -----------------------------
# TOKEN REQUIRED DECORATOR
# -----------------------------
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        # ⭐ Allow Swagger docs to bypass token check FIRST
        public_paths = [
            "/api/docs",
            "/api/docs/",
            "/api/docs/swagger.json",
            "/api/docs/swagger.yaml"
        ]

        if request.path in public_paths or request.path.startswith("/static/swagger"):
            return f(*args, **kwargs)

        # ⭐ Allow login and register routes to bypass token check
        if request.endpoint in ("customers.login_customer", "customers.register_customer"):
            return f(*args, **kwargs)


        token = None

        if "Authorization" in request.headers:
            parts = request.headers["Authorization"].split(" ")
            if len(parts) == 2 and parts[0].lower() == "bearer":
                token = parts[1]

        if not token:
            return jsonify({"message": "Token is missing!"}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = int(data.get("sub"))
            role = data.get("role")

            if not user_id or not role:
                return jsonify({"message": "Invalid token payload"}), 401

        except ExpiredSignatureError:
            return jsonify({"message": "Token has expired!"}), 401

        except JWTError:
            return jsonify({"message": "Invalid token!"}), 401

        return f(user_id, role, *args, **kwargs)

    return decorated
