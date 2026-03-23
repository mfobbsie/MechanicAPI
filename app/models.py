# app/models.py

from datetime import date
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Float, Text, Date, ForeignKey, Table, UniqueConstraint

# Initialize SQLAlchemy using Flask-SQLAlchemy's default Model class
db = SQLAlchemy()


# -----------------------------
# Many-to-many association table
# -----------------------------
mechanic_tickets = Table(
    "mechanic_tickets",
    db.Model.metadata,
    db.Column("mechanic_id", db.Integer, db.ForeignKey("mechanics.id"), primary_key=True),
    db.Column("service_ticket_id", db.Integer, db.ForeignKey("service_tickets.id"), primary_key=True),
)


# -----------------------------
# ROLE MODEL
# -----------------------------
class Role(db.Model):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    role_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    customers: Mapped[list["Customer"]] = relationship("Customer", back_populates="role")
    mechanics: Mapped[list["Mechanic"]] = relationship("Mechanic", back_populates="role")


# -----------------------------
# CUSTOMER MODEL
# -----------------------------
class Customer(db.Model):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)

    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    role: Mapped["Role"] = relationship("Role", back_populates="customers")

    service_tickets: Mapped[list["Service_Tickets"]] = relationship(
        "Service_Tickets",
        back_populates="customer",
        cascade="all, delete-orphan"
    )


# -----------------------------
# SERVICE TICKETS MODEL
# -----------------------------
class Service_Tickets(db.Model):
    __tablename__ = "service_tickets"

    __table_args__ = (
        UniqueConstraint("VIN", "service_date", name="uq_vin_service_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    VIN: Mapped[str] = mapped_column(String(17), nullable=False)
    service_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    customer: Mapped["Customer"] = relationship("Customer", back_populates="service_tickets")

    mechanics: Mapped[list["Mechanic"]] = relationship(
        "Mechanic",
        secondary=mechanic_tickets,
        back_populates="service_tickets"
    )

    inventory_service_tickets: Mapped[list["Inventory_Service_Ticket"]] = relationship(
        "Inventory_Service_Ticket",
        back_populates="service_tickets",
        cascade="all, delete-orphan"
    )


# -----------------------------
# MECHANIC MODEL
# -----------------------------
class Mechanic(db.Model):
    __tablename__ = "mechanics"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    salary: Mapped[float] = mapped_column(Float, nullable=False)

    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    role: Mapped["Role"] = relationship("Role", back_populates="mechanics")

    service_tickets: Mapped[list["Service_Tickets"]] = relationship(
        "Service_Tickets",
        secondary=mechanic_tickets,
        back_populates="mechanics"
    )


# -----------------------------
# INVENTORY MODEL
# -----------------------------
class Inventory(db.Model):
    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)

    inventory_service_tickets: Mapped[list["Inventory_Service_Ticket"]] = relationship(
        "Inventory_Service_Ticket",
        back_populates="inventory",
        cascade="all, delete-orphan"
    )


# -----------------------------
# INVENTORY_SERVICE_TICKET MODEL
# -----------------------------
class Inventory_Service_Ticket(db.Model):
    __tablename__ = "inventory_service_ticket"

    inventory_id: Mapped[int] = mapped_column(ForeignKey("inventory.id"), primary_key=True)
    service_ticket_id: Mapped[int] = mapped_column(ForeignKey("service_tickets.id"), primary_key=True)
    quantity_used: Mapped[int] = mapped_column(Integer, nullable=False)

    inventory: Mapped["Inventory"] = relationship("Inventory", back_populates="inventory_service_tickets")
    service_tickets: Mapped["Service_Tickets"] = relationship("Service_Tickets", back_populates="inventory_service_tickets")


__all__ = [
    "db",
    "Customer",
    "Mechanic",
    "Service_Tickets",
    "Inventory",
    "Inventory_Service_Ticket",
    "Role",
]
