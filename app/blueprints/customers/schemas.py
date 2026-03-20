from app.extensions import ma
from app.models import Customer, db

class CustomerSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Customer
        load_instance = True

customer_schema = CustomerSchema(session=db.session)
customers_schema = CustomerSchema(many=True, session=db.session)