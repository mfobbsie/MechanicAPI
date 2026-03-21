# 🛠️ Mechanics Shop API
A RESTful backend service for managing customers, mechanics, service tickets, inventory, and parts usage in an auto repair shop.

## 📌 Overview
The Mechanics Shop API is a Flask‑based backend designed to simulate a real auto‑shop workflow. It supports:

Customer and mechanic account management

Role‑based access control (admin, mechanic, customer)

Service ticket creation and assignment

Inventory tracking

Adding parts to service tickets

Many‑to‑many relationships (mechanics ↔ tickets, inventory ↔ tickets)

Pagination, rate limiting, and caching

Marshmallow serialization

SQLAlchemy ORM models

MySQL database backend

This project is built using a modern Flask application factory pattern with blueprints and modular architecture.

## 🧱 Tech Stack
Layer	Tools
Backend Framework	Flask
Database	MySQL + SQLAlchemy ORM
Serialization	Marshmallow
Migrations	Flask‑Migrate
Caching	Flask‑Caching
Rate Limiting	Flask‑Limiter
Auth	JWT‑based role‑based access control
Structure	Blueprints + App Factory
## 📂 Project Structure
Code
app/
│
├── blueprints/
│   ├── customers/
│   ├── mechanics/
│   ├── service_tickets/
│   └── inventory/
│
├── models/
├── extensions/
├── cli/
└── config.py
Each domain (customers, mechanics, tickets, inventory) has its own:

routes

schemas

models (if applicable)

This keeps the API modular and scalable.

## 🧩 Core Features
### 👥 Customers
Create customer accounts

Update/delete customer profiles

View customer service history

### 🔧 Mechanics
Create mechanic accounts (admin only)

Assign mechanics to service tickets

View assigned tickets

### 📄 Service Tickets
Create service tickets

Assign mechanics

Add parts used

Track service status

### 📦 Inventory
Add inventory items

Update stock levels

Deduct parts when used

Many‑to‑many relationship with service tickets

## 🔗 Key Endpoints
### Customers
Method	Endpoint	Description
POST	/customers	Create a customer
GET	/customers/	Get customer details
PUT	/customers/	Update customer
DELETE	/customers/	Delete customer
### Mechanics
Method	Endpoint	Description
POST	/mechanics	Create mechanic (admin only)
GET	/mechanics	List mechanics
GET	/mechanics/	Get mechanic details
### Service Tickets
Method	Endpoint	Description
POST	/service_tickets	Create a service ticket
GET	/service_tickets/	Get ticket details
POST	/service_tickets//add_part	Add part to ticket
POST	/service_tickets//assign_mechanic	Assign mechanic
### Inventory
Method	Endpoint	Description
POST	/inventory	Add inventory item
PUT	/inventory/	Update inventory item
GET	/inventory	List inventory
POST	/service_tickets//add_part	Add part to ticket
## 🧪 Example Requests
### Create a Customer
json
POST /customers
{
  "name": "John Doe",
  "phone": "555-1234",
  "email": "john@example.com",
  "password": "password123"
}
### Create a Service Ticket
json
POST /service_tickets
{
  "VIN": "12345678901234567",
  "service_date": "2026-05-12",
  "description": "Brake inspection",
  "customer_id": 1
}
### Add a Part to a Ticket
json
POST /service_tickets/1/add_part
{
  "inventory_id": 1,
  "quantity_used": 2
}
## 🔐 Authentication & Roles
The API uses JWT tokens and enforces role‑based access:

Role	Permissions
Admin	Full access, create mechanics, delete users
Mechanic	View assigned tickets, update ticket status
Customer	View own tickets, update profile
## 🗄️ Database Models (Summary)
Customers
One‑to‑many → Service Tickets

Mechanics
Many‑to‑many → Service Tickets

Inventory
Many‑to‑many → Service Tickets (with quantity_used)

Service Tickets
Central entity connecting customers, mechanics, and parts

## 🚀 Running the App
1. Install dependencies
Code
pip install -r requirements.txt
2. Set up the database
Code
mysql -u root -p
CREATE DATABASE mechanic_db;
3. Run the server
Code
python -m flask run
## 🧹 Future Enhancements
Swagger/OpenAPI documentation

Admin dashboard

Mechanic scheduling system

Customer notifications

Inventory reorder alerts
