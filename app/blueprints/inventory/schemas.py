# app/blueprints/inventory/schemas.py

from app.extensions import ma
from app.models import Inventory, Inventory_Service_Ticket, db
from marshmallow import fields

class InventoryServiceTicketSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Inventory_Service_Ticket
        load_instance = True
        sqla_session = db.session


class InventorySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Inventory
        load_instance = True
        sqla_session = db.session



inventory_schema = InventorySchema()
inventories_schema = InventorySchema(many=True)
