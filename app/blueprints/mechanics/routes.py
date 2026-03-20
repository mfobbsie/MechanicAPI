from flask import request, jsonify
from marshmallow import ValidationError
from app.models import db, Mechanic, Service_Tickets
from app.utils.util import encode_token, token_required

# mechanic schemas
from .schemas import mechanic_schema, mechanics_schema

# service ticket schemas
from app.blueprints.service_tickets.schemas import service_tickets_schema

from . import mechanics_bp

@mechanics_bp.route('/login', methods=['POST'])
def login():
    try:
        credentials = request.json
        username = credentials['email']
        password = credentials['password']
    except KeyError:
        return jsonify({'messages': "Invalid payload, expecting username and password"}), 400
    
    query = db.select(Mechanic).where(Mechanic.email == username)
    mechanic = db.session.execute(query).scalar_one_or_none()
    
    if mechanic and mechanic.password == password:
        auth_token = encode_token(mechanic.id, mechanic.role.role_name)
        
        response = {
            'status': 'success',
            'message': 'Login successful',
            'auth_token': auth_token
        }
        return jsonify(response), 200
    else:
        return jsonify({'message': 'Invalid email or password'}), 401


# Create a new mechanic
@mechanics_bp.route('/', methods=['POST'])
def create_mechanic():
    try:
        mechanic_data = mechanic_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    query = db.select(Mechanic).where(Mechanic.email == mechanic_data.email)
    existing_mechanic = db.session.execute(query).scalars().first()

    if existing_mechanic:
        return jsonify({"message": "Email already associated with an account"}), 400

    db.session.add(mechanic_data)
    db.session.commit()
    return mechanic_schema.jsonify(mechanic_data), 201


# Retrieve all mechanics
@mechanics_bp.route('/', methods=['GET'])
def get_mechanics():
    mechanics = db.session.execute(db.select(Mechanic)).scalars().all()
    return mechanics_schema.jsonify(mechanics), 200


# Retrieve a mechanic by ID
@mechanics_bp.route('/<int:mechanic_id>', methods=['GET'])
def get_mechanic(mechanic_id):
    mechanic = db.session.get(Mechanic, mechanic_id)
    if not mechanic:
        return jsonify({"message": "Mechanic not found"}), 404
    return mechanic_schema.jsonify(mechanic), 200


# Retrieve all service tickets assigned to a mechanic
@mechanics_bp.route('/<int:mechanic_id>/service_tickets', methods=['GET'])
@token_required
def get_mechanic_service_tickets(mechanic_id):
    mechanic = db.session.get(Mechanic, mechanic_id)
    if not mechanic:
        return jsonify({"message": "Mechanic not found"}), 404

    tickets = mechanic.service_tickets
    return service_tickets_schema.jsonify(tickets), 200


# Update a mechanic
@mechanics_bp.route('/<int:mechanic_id>', methods=['PUT'])
@token_required
def update_mechanic(user_id, mechanic_id):
    mechanic = db.session.get(Mechanic, mechanic_id)
    if not mechanic:
        return jsonify({"message": "Mechanic not found"}), 404

    try:
        mechanic_schema.load(request.json, partial=True)
    except ValidationError as err:
        return jsonify(err.messages), 400

    for key, value in request.json.items():
        setattr(mechanic, key, value)

    db.session.commit()
    return mechanic_schema.jsonify(mechanic), 200


# Delete a mechanic
@mechanics_bp.route('/<int:mechanic_id>', methods=['DELETE'])
@token_required
def delete_mechanic(user_id, mechanic_id):
    mechanic = db.session.get(Mechanic, mechanic_id)
    if not mechanic:
        return jsonify({"message": "Mechanic not found"}), 404

    db.session.delete(mechanic)
    db.session.commit()
    return jsonify({"message": "Mechanic deleted successfully"}), 200
