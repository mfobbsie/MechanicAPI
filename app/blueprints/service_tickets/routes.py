from linecache import cache

from flask import request, jsonify
from marshmallow import ValidationError
from app.models import db, Mechanic, Service_Tickets
from .schemas import service_ticket_schema, service_tickets_schema
from . import service_tickets_bp
from app.extensions import limiter

# Create a new service ticket
@service_tickets_bp.route('/', methods=['POST'])
def create_service_ticket():
    try:
        service_ticket_data = service_ticket_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    query = db.select(Service_Tickets).where(
        Service_Tickets.VIN == service_ticket_data.VIN,
        Service_Tickets.service_date == service_ticket_data.service_date
    )

    existing_ticket = db.session.execute(query).scalars().first()

    if existing_ticket:
        return jsonify({
            "message": "A service ticket for this VIN already exists on this date"
        }), 400

    db.session.add(service_ticket_data)
    db.session.commit()
    return service_ticket_schema.jsonify(service_ticket_data), 201


# Retrieve all service tickets
@service_tickets_bp.route('/', methods=['GET'])
@cache.cached(timeout=60)  # Cache this endpoint for 60 seconds
def get_service_tickets():
    tickets = db.session.execute(db.select(Service_Tickets)).scalars().all()
    return service_tickets_schema.jsonify(tickets), 200


# Retrieve a service ticket by ID
@service_tickets_bp.route('/<int:ticket_id>', methods=['GET'])
def get_service_ticket(ticket_id):
    ticket = db.session.get(Service_Tickets, ticket_id)
    if not ticket:
        return jsonify({"message": "Service ticket not found"}), 404
    return service_ticket_schema.jsonify(ticket), 200


# Update a service ticket
@service_tickets_bp.route('/<int:ticket_id>/update', methods=['PUT'])
def update_service_ticket(ticket_id):
    ticket = db.session.get(Service_Tickets, ticket_id)
    if not ticket:
        return jsonify({"message": "Service ticket not found"}), 404

    try:
        service_ticket_schema.load(request.json, partial=True)
    except ValidationError as err:
        return jsonify(err.messages), 400

    for key, value in request.json.items():
        setattr(ticket, key, value)

    db.session.commit()
    return service_ticket_schema.jsonify(ticket), 200


# Assign a mechanic to a service ticket
@service_tickets_bp.route('/<int:ticket_id>/assign_mechanic/<int:mechanic_id>', methods=['POST'])
@limiter.limit("10 per minute")
def assign_mechanic(ticket_id, mechanic_id):
    ticket = db.session.get(Service_Tickets, ticket_id)
    if not ticket:
        return jsonify({"message": "Service ticket not found"}), 404

    mechanic = db.session.get(Mechanic, mechanic_id)
    if not mechanic:
        return jsonify({"message": "Mechanic not found"}), 404

    if mechanic in ticket.mechanics:
        return jsonify({"message": "Mechanic already assigned to this ticket"}), 400

    ticket.mechanics.append(mechanic)
    db.session.commit()

    return jsonify({"message": "Mechanic assigned successfully"}), 200


# Remove a mechanic from a service ticket
@service_tickets_bp.route('/<int:ticket_id>/remove_mechanic/<int:mechanic_id>', methods=['PUT'])
@limiter.limit("10 per minute")
def remove_mechanic(ticket_id, mechanic_id):
    ticket = db.session.get(Service_Tickets, ticket_id)
    if not ticket:
        return jsonify({"message": "Service ticket not found"}), 404

    mechanic = db.session.get(Mechanic, mechanic_id)
    if not mechanic:
        return jsonify({"message": "Mechanic not found"}), 404

    if mechanic not in ticket.mechanics:
        return jsonify({"message": "Mechanic is not assigned to this ticket"}), 400

    ticket.mechanics.remove(mechanic)
    db.session.commit()

    return jsonify({"message": "Mechanic removed successfully"}), 200