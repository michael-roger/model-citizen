from flask import Blueprint, render_template, request, redirect, url_for
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from db import engine

bp = Blueprint('customers', __name__, url_prefix='/customers')

# Helper function to convert empty strings to None
def empty_to_none(value):
    return value if value else None

@bp.route('/')
def list():
    # List all customers
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT id, first_name, last_name, date_of_birth, photo_url FROM customers ORDER BY id ASC"
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
        try:
            with engine.begin() as conn:
                result = conn.execute(text(
                    "INSERT INTO customers (first_name, last_name, date_of_birth, photo_url) "
                    "VALUES (:first_name, :last_name, :date_of_birth, :photo_url) RETURNING id"
                ), data)
                new_cust_id = result.scalar_one()
                for gym_id in selected_gyms:
                    conn.execute(text(
                        "INSERT INTO gym_customer_mappings (gym_id, customer_id, created_datetime_utc) "
                        "VALUES (:gym, :cust, now()) ON CONFLICT (gym_id, customer_id) DO NOTHING"
                    ), {"gym": gym_id, "cust": new_cust_id})
                for trainer_id in selected_trainers:
                    conn.execute(text(
                        "INSERT INTO customer_trainer_mappings (customer_id, trainer_id, created_datetime_utc) "
                        "VALUES (:cust, :trainer, now()) ON CONFLICT (customer_id, trainer_id) DO NOTHING"
                    ), {"cust": new_cust_id, "trainer": trainer_id})
            return redirect(url_for('customers.list'))
        except SQLAlchemyError as e:
            error_msg = "An error occurred while saving the customer. Please check all inputs, especially date of birth."
            return render_template('customers/form.html', customer=data, gyms=gyms, trainers=trainers,
                                   selected_gyms=[int(id) for id in selected_gyms],
                                   selected_trainers=[int(id) for id in selected_trainers],
                                   error=error_msg)
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
        gyms = conn.execute(text("SELECT id, address1, city, state FROM gyms")).mappings().all()
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
            "date_of_birth": empty_to_none(request.form.get('date_of_birth', None)),
            "photo_url": request.form.get('photo_url', '')
        }
        selected_gyms = {int(gym_id) for gym_id in request.form.getlist('gyms')}
        selected_trainers = {int(trainer_id) for trainer_id in request.form.getlist('trainers')}
        # Determine which relationships to add or remove
        to_add_gyms = selected_gyms - current_gyms
        to_remove_gyms = current_gyms - selected_gyms
        to_add_trainers = selected_trainers - current_trainers
        to_remove_trainers = current_trainers - selected_trainers
        try:
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
                        "VALUES (:gym, :cust, now()) "
                        "ON CONFLICT (gym_id, customer_id) DO NOTHING"
                    ), {"gym": gym_id, "cust": customer_id})
                for gym_id in to_remove_gyms:
                    conn.execute(text(
                        "DELETE FROM gym_customer_mappings WHERE gym_id = :gym AND customer_id = :cust"
                    ), {"gym": gym_id, "cust": customer_id})
                # Update trainer relationships
                for trainer_id in to_add_trainers:
                    conn.execute(text(
                        "INSERT INTO customer_trainer_mappings (customer_id, trainer_id, created_datetime_utc) "
                        "VALUES (:cust, :trainer, now()) "
                        "ON CONFLICT (customer_id, trainer_id) DO NOTHING"
                    ), {"cust": customer_id, "trainer": trainer_id})
                for trainer_id in to_remove_trainers:
                    conn.execute(text(
                        "DELETE FROM customer_trainer_mappings WHERE customer_id = :cust AND trainer_id = :trainer"
                    ), {"cust": customer_id, "trainer": trainer_id})
            return redirect(url_for('customers.list'))
        except SQLAlchemyError as e:
            error_msg = "An error occurred while updating the customer. Please check all inputs, especially date of birth."
            return render_template('customers/form.html', customer=data, gyms=gyms, trainers=trainers,
                                selected_gyms=selected_gyms, selected_trainers=selected_trainers,
                                error=error_msg)

    # GET: render form with current data and relationships
    return render_template('customers/form.html', customer=customer, gyms=gyms, trainers=trainers,
                           selected_gyms=current_gyms, selected_trainers=current_trainers)

@bp.route('/<int:customer_id>/delete', methods=['POST'])
def delete(customer_id):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM customers WHERE id = :id"), {"id": customer_id})
    return redirect(url_for('customers.list'))

@bp.route('/<int:customer_id>/view')
def view(customer_id):
    with engine.connect() as conn:
        # Customer core info
        customer = conn.execute(text("SELECT * FROM customers WHERE id = :id"), {"id": customer_id}).mappings().one_or_none()
        if customer is None:
            return redirect(url_for('customers.list'))

        # Associated gyms
        gyms = conn.execute(text("""
            SELECT g.id, g.address1, g.city, g.state
            FROM gym_customer_mappings gcm
            JOIN gyms g ON g.id = gcm.gym_id
            WHERE gcm.customer_id = :id
        """), {"id": customer_id}).mappings().all()

        # Personal trainers
        trainers = conn.execute(text("""
            SELECT t.id, t.first_name, t.last_name, t.photo_url
            FROM customer_trainer_mappings ctm
            JOIN trainers t ON t.id = ctm.trainer_id
            WHERE ctm.customer_id = :id
        """), {"id": customer_id}).mappings().all()

        # Group classes
        classes = conn.execute(text("""
            SELECT gc.id, gc.class_datetime_utc, gct.name AS class_type, g.city AS gym_city
            FROM customer_group_class_mappings cgcm
            JOIN group_classes gc ON gc.id = cgcm.group_class_id
            LEFT JOIN group_class_types gct ON gc.group_class_type_id = gct.id
            LEFT JOIN gyms g ON gc.gym_id = g.id
            WHERE cgcm.customer_id = :id
            ORDER BY gc.class_datetime_utc
        """), {"id": customer_id}).mappings().all()

    return render_template('customers/view.html',
                           customer=customer,
                           gyms=gyms,
                           trainers=trainers,
                           classes=classes)