# app/blueprints/service_tickets/schemas.py

from app.extensions import ma
from app.models import Service_Tickets, db


class ServiceTicketSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Service_Tickets
        load_instance = True
        sqla_session = db.session
        include_fk = True


service_ticket_schema = ServiceTicketSchema()
service_tickets_schema = ServiceTicketSchema(many=True)
