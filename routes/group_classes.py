from flask import Blueprint, render_template, request, redirect, url_for
from sqlalchemy import text
from db import engine

bp = Blueprint('group_classes', __name__, url_prefix='/group_classes')

@bp.route('/')
def list():
    # List classes with joined info (type, gym, trainer names)
    with engine.connect() as conn:
        classes = conn.execute(text(
            "SELECT gc.id, gc.class_datetime_utc, gc.group_class_type_id, gc.gym_id, gc.trainer_id, "
            "gct.name AS class_type_name, gyms.city AS gym_city, "
            "COALESCE(trainers.first_name, '') || ' ' || COALESCE(trainers.last_name, '') AS trainer_name "
            "FROM group_classes gc "
            "LEFT JOIN group_class_types gct ON gc.group_class_type_id = gct.id "
            "LEFT JOIN gyms ON gc.gym_id = gyms.id "
            "LEFT JOIN trainers ON gc.trainer_id = trainers.id"
        )).mappings().all()
    return render_template('group_classes/list.html', group_classes=classes)

@bp.route('/add', methods=['GET', 'POST'])
def add():
    with engine.connect() as conn:
        types = conn.execute(text("SELECT id, name FROM group_class_types")).mappings().all()
        gyms = conn.execute(text("SELECT id, city, state FROM gyms")).mappings().all()
        trainers = conn.execute(text("SELECT id, first_name, last_name FROM trainers")).mappings().all()
        customers = conn.execute(text("SELECT id, first_name, last_name FROM customers")).mappings().all()
    if request.method == 'POST':
        data = {
            "class_datetime_utc": request.form.get('class_datetime_utc', None),
            "group_class_type_id": request.form.get('group_class_type_id', None),
            "gym_id": request.form.get('gym_id', None),
            "trainer_id": request.form.get('trainer_id', None)
        }
        selected_customers = request.form.getlist('customers')  # list of customer IDs
        with engine.begin() as conn:
            result = conn.execute(text(
                "INSERT INTO group_classes (class_datetime_utc, group_class_type_id, gym_id, trainer_id) "
                "VALUES (:class_datetime_utc, :group_class_type_id, :gym_id, :trainer_id) RETURNING id"
            ), data)
            new_class_id = result.scalar_one()
            for cust_id in selected_customers:
                conn.execute(text(
                    "INSERT INTO customer_group_class_mappings (customer_id, group_class_id, created_datetime_utc) "
                    "VALUES (:cust, :class, now())"
                ), {"cust": cust_id, "class": new_class_id})
        return redirect(url_for('group_classes.list'))
    return render_template('group_classes/form.html', group_class=None, types=types, gyms=gyms, trainers=trainers,
                           customers=customers, selected_customers=[])

@bp.route('/<int:class_id>/edit', methods=['GET', 'POST'])
def edit(class_id):
    with engine.connect() as conn:
        group_class = conn.execute(text("SELECT * FROM group_classes WHERE id = :id"), {"id": class_id}) \
            .mappings().one_or_none()
        if group_class is None:
            return redirect(url_for('group_classes.list'))
        types = conn.execute(text("SELECT id, name FROM group_class_types")).mappings().all()
        gyms = conn.execute(text("SELECT id, city, state FROM gyms")).mappings().all()
        trainers = conn.execute(text("SELECT id, first_name, last_name FROM trainers")).mappings().all()
        customers = conn.execute(text("SELECT id, first_name, last_name FROM customers")).mappings().all()
        current_customers = {row['customer_id'] for row in conn.execute(text(
            "SELECT customer_id FROM customer_group_class_mappings WHERE group_class_id = :class"
        ), {"class": class_id}).mappings()}
    if request.method == 'POST':
        data = {
            "id": class_id,
            "class_datetime_utc": request.form.get('class_datetime_utc', None),
            "group_class_type_id": request.form.get('group_class_type_id', None),
            "gym_id": request.form.get('gym_id', None),
            "trainer_id": request.form.get('trainer_id', None)
        }
        selected_customers = set(request.form.getlist('customers'))
        to_add_customers = selected_customers - current_customers
        to_remove_customers = current_customers - selected_customers
        with engine.begin() as conn:
            conn.execute(text(
                "UPDATE group_classes SET class_datetime_utc=:class_datetime_utc, group_class_type_id=:group_class_type_id, "
                "gym_id=:gym_id, trainer_id=:trainer_id WHERE id = :id"
            ), data)
            for cust_id in to_add_customers:
                conn.execute(text(
                    "INSERT INTO customer_group_class_mappings (customer_id, group_class_id, created_datetime_utc) "
                    "VALUES (:cust, :class, now())"
                ), {"cust": cust_id, "class": class_id})
            for cust_id in to_remove_customers:
                conn.execute(text(
                    "DELETE FROM customer_group_class_mappings WHERE customer_id = :cust AND group_class_id = :class"
                ), {"cust": cust_id, "class": class_id})
        return redirect(url_for('group_classes.list'))
    return render_template('group_classes/form.html', group_class=group_class, types=types, gyms=gyms, trainers=trainers,
                           customers=customers, selected_customers=current_customers)

@bp.route('/<int:class_id>/delete', methods=['POST'])
def delete(class_id):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM group_classes WHERE id = :id"), {"id": class_id})
    return redirect(url_for('group_classes.list'))
