# app/blueprints/service_tickets/routes.py

from flask import request, jsonify
from marshmallow import ValidationError
from app.models import db, Mechanic, Service_Tickets
from .schemas import service_ticket_schema, service_tickets_schema
from . import service_tickets_bp
from app.extensions import limiter, cache


# -----------------------------
# CREATE SERVICE TICKET
# -----------------------------
@service_tickets_bp.route('', methods=['POST'])
@service_tickets_bp.route('/', methods=['POST'])
def create_service_ticket():
    try:
        ticket_data = service_ticket_schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    # Check VIN + service_date uniqueness
    existing = db.session.execute(
        db.select(Service_Tickets).where(
            Service_Tickets.VIN == ticket_data.VIN,
            Service_Tickets.service_date == ticket_data.service_date
        )
    ).scalar_one_or_none()

    if existing:
        return jsonify({
            "message": "A service ticket for this VIN already exists on this date"
        }), 400

    db.session.add(ticket_data)
    db.session.commit()

    return service_ticket_schema.jsonify(ticket_data), 201


# -----------------------------
# GET ALL SERVICE TICKETS
# -----------------------------
@service_tickets_bp.route('', methods=['GET'])
@service_tickets_bp.route('/', methods=['GET'])
@cache.cached(timeout=60, query_string=True, unless=lambda: "Authorization" in request.headers)
def get_service_tickets():
    # Read pagination params
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    # Query with pagination
    pagination = db.paginate(
        db.select(Service_Tickets),
        page=page,
        per_page=per_page,
        error_out=False
    )
    tickets = pagination.items
    return jsonify({
        "service_tickets": service_tickets_schema.dump(tickets),
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
# GET SERVICE TICKET BY ID
# -----------------------------
@service_tickets_bp.route('/<int:ticket_id>', methods=['GET'])
def get_service_ticket(ticket_id):
    ticket = db.session.get(Service_Tickets, ticket_id)
    if not ticket:
        return jsonify({"message": "Service ticket not found"}), 404

    return service_ticket_schema.jsonify(ticket), 200


# -----------------------------
# UPDATE SERVICE TICKET
# -----------------------------
@service_tickets_bp.route('/<int:ticket_id>/update', methods=['PUT'])
def update_service_ticket(ticket_id):
    ticket = db.session.get(Service_Tickets, ticket_id)
    if not ticket:
        return jsonify({"message": "Service ticket not found"}), 404

    try:
        service_ticket_schema.load(request.json, partial=True)
    except ValidationError as err:
        return jsonify(err.messages), 400

    # Prevent VIN + date uniqueness violations
    if "VIN" in request.json or "service_date" in request.json:
        new_vin = request.json.get("VIN", ticket.VIN)
        new_date = request.json.get("service_date", ticket.service_date)

        conflict = db.session.execute(
            db.select(Service_Tickets).where(
                Service_Tickets.VIN == new_vin,
                Service_Tickets.service_date == new_date,
                Service_Tickets.id != ticket.id
            )
        ).scalar_one_or_none()

        if conflict:
            return jsonify({
                "message": "Another ticket already exists for this VIN on that date"
            }), 400

    for key, value in request.json.items():
        setattr(ticket, key, value)

    db.session.commit()
    return service_ticket_schema.jsonify(ticket), 200


# -----------------------------
# ASSIGN MECHANIC TO TICKET
# -----------------------------
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


# -----------------------------
# REMOVE MECHANIC FROM TICKET
# -----------------------------
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
