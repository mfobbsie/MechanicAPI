# app/blueprints/customers/routes.py

from flask import request, jsonify
from marshmallow import ValidationError
from app.models import db, Customer, Service_Tickets
from .schemas import customer_schema, customers_schema
from . import customers_bp
from app.utils.util import encode_token, token_required
from app.extensions import limiter, cache

# LOGIN
@customers_bp.route('/login', methods=['POST'])
def login():
    try:
        credentials = request.json
        username = credentials['email']
        password = credentials['password']
    except KeyError:
        return jsonify({'messages': "Invalid payload, expecting username and password"}), 400
    
    query = db.select(Customer).where(Customer.email == username)
    customer = db.session.execute(query).scalar_one_or_none()
    
    if customer and customer.password == password:
        auth_token = encode_token(customer.id, customer.role.role_name)
        return jsonify({
            'status': 'success',
            'message': 'Login successful',
            'auth_token': auth_token
        }), 200
    
    return jsonify({'message': 'Invalid email or password'}), 401


# CREATE CUSTOMER
@customers_bp.route('/', methods=['POST'])
def create_customer():
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    query = db.select(Customer).where(Customer.email == customer_data.email)
    if db.session.execute(query).scalars().first():
        return jsonify({"message": "Email already associated with an account"}), 400

    db.session.add(customer_data)
    db.session.commit()
    return customer_schema.jsonify(customer_data), 201


# GET ALL CUSTOMERS
@customers_bp.route('/', methods=['GET'])
@cache.cached(timeout=60)  # Cache this endpoint for 60 seconds
def get_customers():
    customers = db.session.execute(db.select(Customer)).scalars().all()
    return customers_schema.jsonify(customers), 200


# GET MY TICKETS (AUTH REQUIRED)
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


# UPDATE CUSTOMER
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
        setattr(customer, key, value)

    db.session.commit()
    return customer_schema.jsonify(customer), 200


# DELETE CUSTOMER
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
