# app/blueprints/service_tickets/schemas.py

from app.extensions import ma
from app.models import Service_Tickets, db
from marshmallow import fields
from app.blueprints.inventory.schemas import InventoryServiceTicketSchema

class ServiceTicketSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Service_Tickets
        load_instance = True
        sqla_session = db.session
        include_fk = True

    # Nested relationships
    customer = fields.Nested("CustomerSchema", only=("id", "name", "email"))
    mechanics = fields.Nested("MechanicSchema", many=True, only=("id", "name", "email"))
    inventory_service_tickets = fields.Nested(
        InventoryServiceTicketSchema,
        many=True
    )

service_ticket_schema = ServiceTicketSchema()
service_tickets_schema = ServiceTicketSchema(many=True)

