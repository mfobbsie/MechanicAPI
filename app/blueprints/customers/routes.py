from linecache import cache

from flask import request, jsonify
from marshmallow import ValidationError
from app.models import db, Customer, Service_Tickets
from .schemas import customer_schema, customers_schema
from . import customers_bp
from app.utils.util import encode_token, token_required

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
        
        response = {
            'status': 'success',
            'message': 'Login successful',
            'auth_token': auth_token
        }
        return jsonify(response), 200
    else:
        return jsonify({'message': 'Invalid email or password'}), 401
    
# Create a new customer
@customers_bp.route('/', methods=['POST'])
def create_customer():
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    query = db.select(Customer).where(Customer.email == customer_data.email)
    existing_customer = db.session.execute(query).scalars().first()

    if existing_customer:
        return jsonify({"message": "Email already associated with an account"}), 400

    db.session.add(customer_data)
    db.session.commit()
    return customer_schema.jsonify(customer_data), 201


# Retrieve all customers
@customers_bp.route('/', methods=['GET'])
@cache.cached(timeout=60)  # Cache this endpoint for 60 seconds
def get_customers():
    customers = db.session.execute(db.select(Customer)).scalars().all()
    return customers_schema.jsonify(customers), 200


# Update a customer
@customers_bp.route('/<int:customer_id>', methods=['PUT'])
@token_required
def update_customer(user_id, customer_id):
    customer = db.session.get(Customer, customer_id)
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


# Delete a customer
@customers_bp.route('/<int:customer_id>', methods=['DELETE'])
@token_required
def delete_customer(user_id, customer_id):
    customer = db.session.get(Customer, customer_id)
    if not customer:
        return jsonify({"message": "Customer not found"}), 404

    if customer.service_tickets:
        return jsonify({"message": "Cannot delete customer with existing service tickets"}), 400

    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": "Customer deleted successfully"}), 200
