from flask import request, jsonify
from marshmallow import ValidationError
from app.models import db, Customer, Service_Tickets
from .schemas import customer_schema, customers_schema
from . import customers_bp

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
def get_customers():
    customers = db.session.execute(db.select(Customer)).scalars().all()
    return customers_schema.jsonify(customers), 200


# Update a customer
@customers_bp.route('/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
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
def delete_customer(customer_id):
    customer = db.session.get(Customer, customer_id)
    if not customer:
        return jsonify({"message": "Customer not found"}), 404

    if customer.service_tickets:
        return jsonify({"message": "Cannot delete customer with existing service tickets"}), 400

    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": "Customer deleted successfully"}), 200
