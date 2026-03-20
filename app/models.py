from datetime import date
from flask import app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class Customer(Base):
    __tablename__ = 'customers'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    phone: Mapped[str] = mapped_column(db.String(360), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(db.String(255), nullable=False, unique=True)

    service_tickets: Mapped[list["Service_Tickets"]] = db.relationship(
        "Service_Tickets",
        back_populates="customer"
    )


# Junction table (many-to-many)
mechanic_tickets = db.Table(
    'mechanic_tickets',
    db.Column('mechanic_id', db.Integer, db.ForeignKey('mechanics.id'), primary_key=True),
    db.Column('service_ticket_id', db.Integer, db.ForeignKey('service_tickets.id'), primary_key=True)
)

class Service_Tickets(Base):
    __tablename__ = 'service_tickets'
    __table_args__ = (
        db.UniqueConstraint('VIN', 'service_date', name='uq_vin_service_date'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    VIN: Mapped[str] = mapped_column(db.String(17), nullable=False)
    service_date: Mapped[date] = mapped_column(db.Date, nullable=False)
    description: Mapped[str] = mapped_column(db.Text, nullable=False)
    customer_id: Mapped[int] = mapped_column(db.ForeignKey('customers.id'))

    customer: Mapped["Customer"] = db.relationship(
        "Customer",
        back_populates="service_tickets"
    )

    mechanics: Mapped[list["Mechanic"]] = db.relationship(
        "Mechanic",
        secondary=mechanic_tickets,
        back_populates="service_tickets"
    )

class Mechanic(Base):
    __tablename__ = 'mechanics'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    phone: Mapped[str] = mapped_column(db.String(360), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(db.String(255), nullable=False, unique=True)
    salary: Mapped[float] = mapped_column(db.Float, nullable=False)

    service_tickets: Mapped[list["Service_Tickets"]] = db.relationship(
        "Service_Tickets",
        secondary=mechanic_tickets,
        back_populates="mechanics"
    )