from app.extensions import ma
from app.models import Mechanic, db

class MechanicSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Mechanic
        load_instance = True

mechanic_schema = MechanicSchema(session=db.session)
mechanics_schema = MechanicSchema(many=True, session=db.session)
