# app/blueprints/mechanics/routes.py

from flask import request, jsonify
from marshmallow import ValidationError
from werkzeug.security import check_password_hash
from app.models import db, Mechanic, Service_Tickets
from .schemas import mechanic_schema, mechanics_schema
from app.blueprints.service_tickets.schemas import service_tickets_schema
from . import mechanics_bp
from app.utils.util import encode_token, token_required
from werkzeug.security import generate_password_hash, check_password_hash

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
@mechanics_bp.route('/', methods=['POST'])
@token_required
def create_mechanic(user_id, role):

    print("Loaded schema fields:", mechanic_schema.fields.keys())

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
    mechanic_data.password = generate_password_hash(mechanic_data.password)

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
@mechanics_bp.route('/', methods=['GET'])
def get_mechanics():
    mechanics = db.session.execute(db.select(Mechanic)).scalars().all()
    return mechanics_schema.jsonify(mechanics), 200


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
# UPDATE MECHANIC
# -----------------------------
@mechanics_bp.route('/', methods=['PUT'])
@token_required
def update_mechanic(user_id, role):
    if role != "mechanic":
        return jsonify({"message": "Unauthorized"}), 403

    mechanic = db.session.get(Mechanic, user_id)
    if not mechanic:
        return jsonify({"message": "Mechanic not found"}), 404

    try:
        mechanic_schema.load(request.json, partial=True)
    except ValidationError as err:
        return jsonify(err.messages), 400

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

    return jsonify({"message": "Mechanic deleted successfully"}), 200
