# app/blueprints/mechanics/schemas.py

from app.extensions import ma
from app.models import Mechanic, db
from marshmallow import fields

class MechanicSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Mechanic
        load_instance = True
        sqla_session = db.session
        load_only = ("password",)  # allow password on input, never output it

    password = fields.String(load_only=True)


mechanic_schema = MechanicSchema()
mechanics_schema = MechanicSchema(many=True)
