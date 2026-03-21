# app/blueprints/customers/routes.py

from flask import request, jsonify
from marshmallow import ValidationError
from werkzeug.security import check_password_hash
from app.models import db, Customer, Service_Tickets
from .schemas import customer_schema, customers_schema
from . import customers_bp
from app.utils.util import encode_token, token_required
from app.extensions import cache
from werkzeug.security import generate_password_hash, check_password_hash


# -----------------------------
# LOGIN
# -----------------------------
@customers_bp.route('/login', methods=['POST'])
def login_customer():

    data = request.get_json() or {}

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"message": "Email and password are required"}), 400

    customer = db.session.execute(
        db.select(Customer).where(Customer.email == email)
    ).scalar_one_or_none()

    if not customer:
        return jsonify({"message": "Invalid email or password"}), 401

    # Check hashed password
    if not check_password_hash(customer.password, password):
        return jsonify({"message": "Invalid email or password"}), 401

    # IMPORTANT:
    # Allow BOTH admin and customer to log in
    role_name = customer.role.role_name

    token = encode_token(customer.id, role_name)

    return jsonify({
        "status": "success",
        "message": "Login successful",
        "auth_token": token
    }), 200
# -----------------------------
# CREATE CUSTOMER
# -----------------------------
@customers_bp.route('/', methods=['POST'])
def create_customer():
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    # -----------------------------
    # HASH PASSWORD BEFORE SAVING
    # -----------------------------
    customer_data.password = generate_password_hash(customer_data.password)

    # Check duplicate email
    existing = db.session.execute(
        db.select(Customer).where(Customer.email == customer_data.email)
    ).scalar_one_or_none()

    if existing:
        return jsonify({"message": "Email already associated with an account"}), 400

    # Assign default customer role
    from app.models import Role
    customer_role = db.session.execute(
        db.select(Role).where(Role.role_name == "customer")
    ).scalar_one_or_none()

    if not customer_role:
        return jsonify({"message": "Customer role not found"}), 500

    customer_data.role_id = customer_role.id

    db.session.add(customer_data)
    db.session.commit()

    return customer_schema.jsonify(customer_data), 201

# -----------------------------
# GET ALL CUSTOMERS
# -----------------------------
@customers_bp.route('/', methods=['GET'])
@cache.cached(timeout=60)
def get_customers():
    customers = db.session.execute(db.select(Customer)).scalars().all()
    return customers_schema.jsonify(customers), 200


# -----------------------------
# GET MY TICKETS (AUTH REQUIRED)
# -----------------------------
@customers_bp.route('/my-tickets', methods=['GET'])
@token_required
@cache.cached(timeout=60)
def get_my_tickets(user_id, role):
    if role != "customer":
        return jsonify({"message": "Unauthorized"}), 403

    tickets = db.session.execute(
        db.select(Service_Tickets).where(Service_Tickets.customer_id == user_id)
    ).scalars().all()

    return jsonify({
        "customer_id": user_id,
        "tickets": [
            {
                "id": t.id,
                "VIN": t.VIN,
                "service_date": t.service_date.isoformat(),
                "description": t.description,
                "mechanics": [m.name for m in t.mechanics]
            }
            for t in tickets
        ]
    }), 200


# -----------------------------
# UPDATE CUSTOMER
# -----------------------------
@customers_bp.route('/', methods=['PUT'])
@token_required
def update_customer(user_id, role):
    if role != "customer":
        return jsonify({"message": "Unauthorized"}), 403

    customer = db.session.get(Customer, user_id)
    if not customer:
        return jsonify({"message": "Customer not found"}), 404

    try:
        customer_schema.load(request.json, partial=True)
    except ValidationError as err:
        return jsonify(err.messages), 400

    for key, value in request.json.items():
        if key == "password":
            # Password hashing handled in schema or here if needed
            continue
        setattr(customer, key, value)

    db.session.commit()
    return customer_schema.jsonify(customer), 200


# -----------------------------
# DELETE CUSTOMER
# -----------------------------
@customers_bp.route('/', methods=['DELETE'])
@token_required
def delete_customer(user_id, role):
    if role != "customer":
        return jsonify({"message": "Unauthorized"}), 403

    customer = db.session.get(Customer, user_id)
    if not customer:
        return jsonify({"message": "Customer not found"}), 404

    if customer.service_tickets:
        return jsonify({"message": "Cannot delete customer with existing service tickets"}), 400

    db.session.delete(customer)
    db.session.commit()

    return jsonify({"message": "Customer deleted successfully"}), 200
