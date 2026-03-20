from app.models import db
from app.extensions import ma
from app.models import Service_Tickets

class ServiceTicketSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Service_Tickets
        load_instance = True
        include_fk = True
        sqla_session = db.session   # optional but recommended

service_ticket_schema = ServiceTicketSchema(session=db.session)
service_tickets_schema = ServiceTicketSchema(many=True, session=db.session)
