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
@customers_bp.route('', methods=['POST'])
def create_customer():
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    # -----------------------------
    # HASH PASSWORD BEFORE SAVING
    # -----------------------------
    customer_data.password = generate_password_hash(
    customer_data.password,
    method="pbkdf2:sha256"
    )

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
# GET ALL CUSTOMERS (PAGINATED)
# -----------------------------
@customers_bp.route('', methods=['GET'])
@cache.cached(timeout=60, query_string=True, unless=lambda: "Authorization" in request.headers)

def get_customers():
    # Read pagination params
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    # Query with pagination
    pagination = db.paginate(
        db.select(Customer),
        page=page,
        per_page=per_page,
        error_out=False
    )

    customers = pagination.items

    return jsonify({
        "customers": customers_schema.dump(customers),
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev,
        "next_page": pagination.next_num if pagination.has_next else None,
        "prev_page": pagination.prev_num if pagination.has_prev else None
    }), 200

# -----------------------------
# GET MY TICKETS (AUTH REQUIRED)
# -----------------------------
@customers_bp.route('/my-tickets', methods=['GET'])
@token_required
@cache.cached(timeout=60, query_string=True, unless=lambda: "Authorization" in request.headers)
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
# UPDATE CUSTOMER (AUTH REQUIRED)
# -----------------------------

@customers_bp.route('/<int:customer_id>', methods=['PUT'])
@token_required
def update_customer(user_id, role, customer_id):

    # ⭐ Admins can update any customer
    if role == "admin":
        customer = db.session.get(Customer, customer_id)
        if not customer:
            return jsonify({"message": "Customer not found"}), 404

        try:
            customer_schema.load(request.json, partial=True)
        except ValidationError as err:
            return jsonify(err.messages), 400

        for key, value in request.json.items():
            if key == "password":
                customer.password = generate_password_hash(value, method="pbkdf2:sha256")
            else:
                setattr(customer, key, value)

        db.session.commit()
        return customer_schema.jsonify(customer), 200

    # ⭐ Customers can update only themselves
    if role == "customer" and user_id == customer_id:
        customer = db.session.get(Customer, customer_id)
        if not customer:
            return jsonify({"message": "Customer not found"}), 404

        try:
            customer_schema.load(request.json, partial=True)
        except ValidationError as err:
            return jsonify(err.messages), 400

        for key, value in request.json.items():
            if key == "password":
                customer.password = generate_password_hash(value, method="pbkdf2:sha256")
            else:
                setattr(customer, key, value)

        db.session.commit()
        return customer_schema.jsonify(customer), 200

    # ⭐ Everyone else → unauthorized
    return jsonify({"message": "Unauthorized"}), 403

# -----------------------------
# DELETE CUSTOMER (AUTH REQUIRED)
# -----------------------------
@customers_bp.route('/<int:customer_id>', methods=['DELETE'])
@token_required
def delete_customer(user_id, role, customer_id):

    # ⭐ Admins can delete any customer
    if role == "admin":
        customer = db.session.get(Customer, customer_id)
        if not customer:
            return jsonify({"message": "Customer not found"}), 404

        if customer.service_tickets:
            return jsonify({"message": "Cannot delete customer with existing service tickets"}), 400

        db.session.delete(customer)
        db.session.commit()
        return jsonify({"message": f"Customer {customer_id} deleted successfully"}), 200

    # ⭐ Customers can delete ONLY themselves
    if role == "customer" and user_id == customer_id:
        customer = db.session.get(Customer, customer_id)
        if not customer:
            return jsonify({"message": "Customer not found"}), 404

        if customer.service_tickets:
            return jsonify({"message": "Cannot delete customer with existing service tickets"}), 400

        db.session.delete(customer)
        db.session.commit()
        return jsonify({"message": "Your account has been deleted"}), 200

    # ⭐ Everyone else → unauthorized
    return jsonify({"message": "Unauthorized"}), 403
