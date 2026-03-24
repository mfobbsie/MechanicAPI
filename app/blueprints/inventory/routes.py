# app/blueprints/inventory/routes.py

from flask import request, jsonify
from app.models import (
    db,
    Inventory,
    Inventory_Service_Ticket,
    Service_Tickets
)
from .schemas import inventory_schema, inventories_schema
from app.blueprints.inventory import inventory_bp
from app.blueprints.service_tickets import service_tickets_bp


# ----------------------------------------
# CREATE INVENTORY ITEM
# ----------------------------------------
@inventory_bp.route('', methods=['POST'])
@inventory_bp.route('/', methods=['POST'])
def create_inventory_item():
    data = request.get_json()

    item = Inventory(
        item_name=data.get("item_name"),
        quantity=data.get("quantity"),
        price=data.get("price")
    )

    db.session.add(item)
    db.session.commit()

    return inventory_schema.jsonify(item), 201


# ----------------------------------------
# GET ALL INVENTORY ITEMS (PAGINATED)
# ----------------------------------------
@inventory_bp.route('', methods=['GET'])
@inventory_bp.route('/', methods=['GET'])
def get_inventory():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    pagination = db.paginate(
        db.select(Inventory),
        page=page,
        per_page=per_page,
        error_out=False
    )

    items = pagination.items

    return jsonify({
        "inventory": inventories_schema.dump(items),
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages
    }), 200


# ----------------------------------------
# GET SINGLE INVENTORY ITEM
# ----------------------------------------
@inventory_bp.route('/<int:item_id>', methods=['GET'])
def get_inventory_item(item_id):
    item = db.session.get(Inventory, item_id)

    if not item:
        return jsonify({"message": "Item not found"}), 404

    return inventory_schema.jsonify(item), 200


# ----------------------------------------
# UPDATE INVENTORY ITEM
# ----------------------------------------
@inventory_bp.route('/<int:item_id>', methods=['PUT'])
def update_inventory_item(item_id):
    item = db.session.get(Inventory, item_id)

    if not item:
        return jsonify({"message": "Item not found"}), 404

    data = request.get_json()

    item.item_name = data.get("item_name", item.item_name)
    item.quantity = data.get("quantity", item.quantity)
    item.price = data.get("price", item.price)

    db.session.commit()

    return inventory_schema.jsonify(item), 200


# ----------------------------------------
# DELETE INVENTORY ITEM
# ----------------------------------------
@inventory_bp.route('/<int:item_id>', methods=['DELETE'])
def delete_inventory_item(item_id):
    item = db.session.get(Inventory, item_id)

    if not item:
        return jsonify({"message": "Item not found"}), 404

    db.session.delete(item)
    db.session.commit()

    return jsonify({"message": "Item deleted"}), 200


# ============================================================
# ADD PART TO A SERVICE TICKET
# ============================================================
@service_tickets_bp.route('/<int:ticket_id>/add_part', methods=['POST'])
def add_part_to_ticket(ticket_id):
    ticket = db.session.get(Service_Tickets, ticket_id)
    if not ticket:
        return jsonify({"message": "Service ticket not found"}), 404

    data = request.get_json()
    inventory_id = data.get("inventory_id")
    quantity_used = data.get("quantity_used", 1)

    part = db.session.get(Inventory, inventory_id)
    if not part:
        return jsonify({"message": "Inventory item not found"}), 404

    # Check stock
    if part.quantity < quantity_used:
        return jsonify({"message": "Not enough stock"}), 400

    # Reduce inventory
    part.quantity -= quantity_used

    # Create junction record
    link = Inventory_Service_Ticket(
        inventory_id=inventory_id,
        service_ticket_id=ticket_id,
        quantity_used=quantity_used
    )

    db.session.add(link)
    db.session.commit()

    return jsonify({"message": "Part added to ticket"}), 201