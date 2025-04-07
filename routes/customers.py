from flask import Blueprint, render_template, request, redirect, url_for
from sqlalchemy import text
from db import engine

bp = Blueprint('customers', __name__, url_prefix='/customers')

@bp.route('/')
def list():
    # List all customers
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT id, first_name, last_name, date_of_birth, photo_url FROM customers"
        ))
        customers = result.mappings().all()
    return render_template('customers/list.html', customers=customers)

@bp.route('/add', methods=['GET', 'POST'])
def add():
    # Fetch options for related multi-selects
    with engine.connect() as conn:
        gyms = conn.execute(text("SELECT id, address1, city, state FROM gyms")).mappings().all()
        trainers = conn.execute(text("SELECT id, first_name, last_name FROM trainers")).mappings().all()
    if request.method == 'POST':
        data = {
            "first_name": request.form.get('first_name', ''),
            "last_name": request.form.get('last_name', ''),
            "date_of_birth": request.form.get('date_of_birth', None),
            "photo_url": request.form.get('photo_url', '')
        }
        selected_gyms = request.form.getlist('gyms')            # list of gym IDs
        selected_trainers = request.form.getlist('trainers')    # list of trainer IDs
        with engine.begin() as conn:
            # Insert new customer
            result = conn.execute(text(
                "INSERT INTO customers (first_name, last_name, date_of_birth, photo_url) "
                "VALUES (:first_name, :last_name, :date_of_birth, :photo_url) RETURNING id"
            ), data)
            new_cust_id = result.scalar_one()
            # Insert customer-gym relationships
            for gym_id in selected_gyms:
                conn.execute(text(
                    "INSERT INTO gym_customer_mappings (gym_id, customer_id, created_datetime_utc) "
                    "VALUES (:gym, :cust, now()) "
                    "ON CONFLICT (gym_id, customer_id) DO NOTHING"
                ), {"gym": gym_id, "cust": new_cust_id})
            # Insert customer-trainer relationships
            for trainer_id in selected_trainers:
                conn.execute(text(
                    "INSERT INTO customer_trainer_mappings (customer_id, trainer_id, created_datetime_utc) "
                    "VALUES (:cust, :trainer, now()) "
                    "ON CONFLICT (customer_id, trainer_id) DO NOTHING"
                ), {"cust": new_cust_id, "trainer": trainer_id})
        return redirect(url_for('customers.list'))
    # GET: display form
    return render_template('customers/form.html', customer=None, gyms=gyms, trainers=trainers,
                           selected_gyms=[], selected_trainers=[])

@bp.route('/<int:customer_id>/edit', methods=['GET', 'POST'])
def edit(customer_id):
    with engine.connect() as conn:
        customer = conn.execute(text("SELECT * FROM customers WHERE id = :id"), {"id": customer_id}) \
            .mappings().one_or_none()
        if customer is None:
            return redirect(url_for('customers.list'))
        gyms = conn.execute(text("SELECT id,  city, state FROM gyms")).mappings().all()
        trainers = conn.execute(text("SELECT id, first_name, last_name FROM trainers")).mappings().all()
        # Current related gyms and trainers for this customer
        current_gyms = {row['gym_id'] for row in conn.execute(text(
            "SELECT gym_id FROM gym_customer_mappings WHERE customer_id = :cust"
        ), {"cust": customer_id}).mappings()}
        current_trainers = {row['trainer_id'] for row in conn.execute(text(
            "SELECT trainer_id FROM customer_trainer_mappings WHERE customer_id = :cust"
        ), {"cust": customer_id}).mappings()}
    if request.method == 'POST':
        data = {
            "id": customer_id,
            "first_name": request.form.get('first_name', ''),
            "last_name": request.form.get('last_name', ''),
            "date_of_birth": request.form.get('date_of_birth', None),
            "photo_url": request.form.get('photo_url', '')
        }
        selected_gyms = set(request.form.getlist('gyms'))
        selected_trainers = set(request.form.getlist('trainers'))
        # Determine which relationships to add or remove
        to_add_gyms = selected_gyms - current_gyms
        to_remove_gyms = current_gyms - selected_gyms
        to_add_trainers = selected_trainers - current_trainers
        to_remove_trainers = current_trainers - selected_trainers
        with engine.begin() as conn:
            # Update customer info
            conn.execute(text(
                "UPDATE customers SET first_name=:first_name, last_name=:last_name, "
                "date_of_birth=:date_of_birth, photo_url=:photo_url WHERE id = :id"
            ), data)
            # Update gym relationships
            for gym_id in to_add_gyms:
                conn.execute(text(
                    "INSERT INTO gym_customer_mappings (gym_id, customer_id, created_datetime_utc) "
                    "VALUES (:gym, :cust, now())"
                ), {"gym": gym_id, "cust": customer_id})
            for gym_id in to_remove_gyms:
                conn.execute(text(
                    "DELETE FROM gym_customer_mappings WHERE gym_id = :gym AND customer_id = :cust"
                ), {"gym": gym_id, "cust": customer_id})
            # Update trainer relationships
            for trainer_id in to_add_trainers:
                conn.execute(text(
                    "INSERT INTO customer_trainer_mappings (customer_id, trainer_id, created_datetime_utc) "
                    "VALUES (:cust, :trainer, now())"
                ), {"cust": customer_id, "trainer": trainer_id})
            for trainer_id in to_remove_trainers:
                conn.execute(text(
                    "DELETE FROM customer_trainer_mappings WHERE customer_id = :cust AND trainer_id = :trainer"
                ), {"cust": customer_id, "trainer": trainer_id})
        return redirect(url_for('customers.list'))
    # GET: render form with current data and relationships
    return render_template('customers/form.html', customer=customer, gyms=gyms, trainers=trainers,
                           selected_gyms=current_gyms, selected_trainers=current_trainers)

@bp.route('/<int:customer_id>/delete', methods=['POST'])
def delete(customer_id):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM customers WHERE id = :id"), {"id": customer_id})
    return redirect(url_for('customers.list'))
