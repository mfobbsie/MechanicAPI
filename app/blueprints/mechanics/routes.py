# app/blueprints/mechanics/routes.py

from app import cache
from flask import request, jsonify
from marshmallow import ValidationError
from app.models import db, Mechanic, Service_Tickets, mechanic_tickets
from .schemas import mechanic_schema, mechanics_schema
from app.blueprints.service_tickets.schemas import service_tickets_schema
from . import mechanics_bp
from app.utils.util import encode_token, token_required
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func

# -----------------------------
# LOGIN
# -----------------------------
@mechanics_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"message": "Email and password are required"}), 400

    mechanic = db.session.execute(
        db.select(Mechanic).where(Mechanic.email == email)
    ).scalar_one_or_none()

    if mechanic and check_password_hash(mechanic.password, password):
        token = encode_token(mechanic.id, mechanic.role.role_name)
        return jsonify({
            "status": "success",
            "message": "Login successful",
            "auth_token": token
        }), 200

    return jsonify({"message": "Invalid email or password"}), 401


# -----------------------------
# CREATE MECHANIC (ADMIN ONLY)
# -----------------------------
@mechanics_bp.route('', methods=['POST'])
@token_required
def create_mechanic(user_id, role):

    print("ROLE RECEIVED IN ROUTE:", role)

    if role != "admin":
        return jsonify({"message": "Unauthorized"}), 403

    try:
        mechanic_data = mechanic_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    # Check for duplicate email
    existing = db.session.execute(
        db.select(Mechanic).where(Mechanic.email == mechanic_data.email)
    ).scalar_one_or_none()

    if existing:
        return jsonify({"message": "Email already associated with an account"}), 400

    # -----------------------------
    # HASH PASSWORD BEFORE SAVING
    # -----------------------------
    mechanic_data.password = generate_password_hash(
    mechanic_data.password,
    method="pbkdf2:sha256"
    )

    # -----------------------------
    # ASSIGN MECHANIC ROLE HERE
    # -----------------------------
    from app.models import Role
    mechanic_role = db.session.execute(
        db.select(Role).where(Role.role_name == "mechanic")
    ).scalar_one_or_none()

    if not mechanic_role:
        return jsonify({"message": "Mechanic role not found"}), 500

    mechanic_data.role_id = mechanic_role.id

    db.session.add(mechanic_data)
    db.session.commit()

    return mechanic_schema.jsonify(mechanic_data), 201

# -----------------------------
# GET ALL MECHANICS
# -----------------------------
@mechanics_bp.route('', methods=['GET'])
@cache.cached(timeout=60, query_string=True, unless=lambda: "Authorization" in request.headers)
def get_mechanics():
    # Read pagination params
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    # Query with pagination
    pagination = db.paginate(
        db.select(Mechanic),
        page=page,
        per_page=per_page,
        error_out=False
    )

    mechanics = pagination.items
    return jsonify({
        "mechanics": mechanics_schema.dump(mechanics),
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
# GET MECHANIC BY ID
# -----------------------------
@mechanics_bp.route('/<int:mechanic_id>', methods=['GET'])
def get_mechanic(mechanic_id):
    mechanic = db.session.get(Mechanic, mechanic_id)
    if not mechanic:
        return jsonify({"message": "Mechanic not found"}), 404

    return mechanic_schema.jsonify(mechanic), 200


# -----------------------------
# GET MECHANIC'S TICKETS
# -----------------------------
@mechanics_bp.route('/<int:mechanic_id>/service_tickets', methods=['GET'])
@token_required
def get_mechanic_service_tickets(user_id, role, mechanic_id):
    if role not in ("mechanic", "admin"):
        return jsonify({"message": "Unauthorized"}), 403

    mechanic = db.session.get(Mechanic, mechanic_id)
    if not mechanic:
        return jsonify({"message": "Mechanic not found"}), 404

    return service_tickets_schema.jsonify(mechanic.service_tickets), 200
# -----------------------------
# GET LIST OF MOST POPULAR MECHANIC
# -----------------------------
@mechanics_bp.route('/popular', methods=['GET'])
@token_required
def popular_mechanics(user_id, role):

    # Only admin should see this
    if role != "admin":
        return jsonify({"message": "Unauthorized"}), 403

    results = (
        db.session.query(
            Mechanic,
            func.count(mechanic_tickets.c.service_ticket_id).label("ticket_count")
        )
        .outerjoin(mechanic_tickets, Mechanic.id == mechanic_tickets.c.mechanic_id)
        .group_by(Mechanic.id)
        .order_by(func.count(mechanic_tickets.c.service_ticket_id).desc())
        .all()
    )

    response = [
        {
            "id": mechanic.id,
            "name": mechanic.name,
            "email": mechanic.email,
            "ticket_count": ticket_count
        }
        for mechanic, ticket_count in results
    ]

    return jsonify(response), 200
# -----------------------------
# UPDATE MECHANIC
# -----------------------------
@mechanics_bp.route('', methods=['PUT'])
@token_required
def update_mechanic(user_id, role):

    # ⭐ Admins can update ANY mechanic (must specify mechanic_id in body)
    if role == "admin":
        mechanic_id = request.json.get("id")
        if not mechanic_id:
            return jsonify({"message": "Mechanic ID required for admin update"}), 400

        mechanic = db.session.get(Mechanic, mechanic_id)
        if not mechanic:
            return jsonify({"message": "Mechanic not found"}), 404

    # ⭐ Mechanics can update ONLY themselves
    elif role == "mechanic":
        mechanic = db.session.get(Mechanic, user_id)
        if not mechanic:
            return jsonify({"message": "Mechanic not found"}), 404

    else:
        return jsonify({"message": "Unauthorized"}), 403

    # Load + validate
    try:
        mechanic_schema.load(request.json, partial=True)
    except ValidationError as err:
        return jsonify(err.messages), 400

    # Apply updates
    for key, value in request.json.items():
        if key == "password":
            mechanic.password = generate_password_hash(value)
        else:
            setattr(mechanic, key, value)

    db.session.commit()
    return mechanic_schema.jsonify(mechanic), 200

# -----------------------------
# DELETE MECHANIC (ADMIN ONLY)
# -----------------------------
@mechanics_bp.route('/<int:mechanic_id>', methods=['DELETE'])
@token_required
def delete_mechanic(user_id, role, mechanic_id):
    if role != "admin":
        return jsonify({"message": "Unauthorized"}), 403

    mechanic = db.session.get(Mechanic, mechanic_id)
    if not mechanic:
        return jsonify({"message": "Mechanic not found"}), 404

    db.session.delete(mechanic)
    db.session.commit()

    return jsonify({"message": f"Mechanic {mechanic_id} deleted successfully"}), 200
