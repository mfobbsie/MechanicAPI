from app.extensions import ma
from app.models import Customer, db
from marshmallow import fields

class CustomerSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Customer
        load_instance = True
        sqla_session = db.session
        load_only = ("password",)  # allow password input, hide on output

    name = fields.String(required=True)
    email = fields.Email(required=True)
    password = fields.String(load_only=True)
    phone = fields.String(required=True)


customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)

