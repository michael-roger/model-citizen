from flask import Blueprint, render_template, request, redirect, url_for
from sqlalchemy import text
from db import engine

bp = Blueprint('gyms', __name__, url_prefix='/gyms')

@bp.route('/')
def list():
    # List all gyms
    with engine.connect() as conn:
        gyms = conn.execute(text("SELECT * FROM gyms ORDER BY id ASC")).mappings().all()
    return render_template('gyms/list.html', gyms=gyms)

@bp.route('/add', methods=['GET', 'POST'])
def add():
    # Fetch lists of related entities for multi-selects
    with engine.connect() as conn:
        amenities = conn.execute(text("SELECT id, name FROM amenities")).mappings().all()
        trainers = conn.execute(text("SELECT id, first_name, last_name FROM trainers")).mappings().all()
        customers = conn.execute(text("SELECT id, first_name, last_name FROM customers")).mappings().all()
    if request.method == 'POST':
        data = {
            "address1": request.form.get('address1', ''),
            "address2": request.form.get('address2', ''),
            "city": request.form.get('city', ''),
            "state": request.form.get('state', ''),
            "zip": request.form.get('zip', ''),
            "photo_url": request.form.get('photo_url', '')
        }
        selected_amenities = request.form.getlist('amenities')  # amenity IDs
        selected_trainers = request.form.getlist('trainers')    # trainer IDs
        selected_customers = request.form.getlist('customers')  # customer IDs
        with engine.begin() as conn:
            # Insert new gym
            result = conn.execute(text(
                "INSERT INTO gyms (address1, address2, city, state, zip, photo_url) "
                "VALUES (:address1, :address2, :city, :state, :zip, :photo_url) RETURNING id"
            ), data)
            new_gym_id = result.scalar_one()
            # Insert gym-amenity mappings
            for amen_id in selected_amenities:
                conn.execute(text(
                    "INSERT INTO gym_amenity_mappings (gym_id, amenity_id) "
                    "VALUES (:gym, :amen) "
                    "ON CONFLICT (gym_id, amenity_id) DO NOTHING"
                ), {"gym": new_gym_id, "amen": amen_id})
            # Insert gym-trainer mappings
            for trainer_id in selected_trainers:
                conn.execute(text(
                    "INSERT INTO gym_trainer_mappings (gym_id, trainer_id) "
                    "VALUES (:gym, :trainer) "
                    "ON CONFLICT (gym_id, trainer_id) DO NOTHING"
                ), {"gym": new_gym_id, "trainer": trainer_id})
            # Insert gym-customer mappings
            for cust_id in selected_customers:
                conn.execute(text(
                    "INSERT INTO gym_customer_mappings (gym_id, customer_id, created_datetime_utc) "
                    "VALUES (:gym, :cust, now()) "
                    "ON CONFLICT (gym_id, customer_id) DO NOTHING"
                ), {"gym": new_gym_id, "cust": cust_id})
        return redirect(url_for('gyms.list'))
    # GET: render form
    return render_template('gyms/form.html', gym=None, amenities=amenities, trainers=trainers, customers=customers,
                           selected_amenities=[], selected_trainers=[], selected_customers=[])

@bp.route('/<int:gym_id>/edit', methods=['GET', 'POST'])
def edit(gym_id):
    with engine.connect() as conn:
        gym = conn.execute(text("SELECT * FROM gyms WHERE id = :id"), {"id": gym_id}).mappings().one_or_none()
        if gym is None:
            return redirect(url_for('gyms.list'))
        amenities = conn.execute(text("SELECT id, name FROM amenities")).mappings().all()
        trainers = conn.execute(text("SELECT id, first_name, last_name FROM trainers")).mappings().all()
        customers = conn.execute(text("SELECT id, first_name, last_name FROM customers")).mappings().all()
        # Current related items
        current_amenities = {row['amenity_id'] for row in conn.execute(text(
            "SELECT amenity_id FROM gym_amenity_mappings WHERE gym_id = :gym"
        ), {"gym": gym_id}).mappings()}
        current_trainers = {row['trainer_id'] for row in conn.execute(text(
            "SELECT trainer_id FROM gym_trainer_mappings WHERE gym_id = :gym"
        ), {"gym": gym_id}).mappings()}
        current_customers = {row['customer_id'] for row in conn.execute(text(
            "SELECT customer_id FROM gym_customer_mappings WHERE gym_id = :gym"
        ), {"gym": gym_id}).mappings()}
    if request.method == 'POST':
        data = {
            "id": gym_id,
            "address1": request.form.get('address1', ''),
            "address2": request.form.get('address2', ''),
            "city": request.form.get('city', ''),
            "state": request.form.get('state', ''),
            "zip": request.form.get('zip', ''),
            "photo_url": request.form.get('photo_url', '')
        }
        selected_amenities = set(request.form.getlist('amenities'))
        selected_trainers = set(request.form.getlist('trainers'))
        selected_customers = set(request.form.getlist('customers'))
        # Determine changes for each mapping
        to_add_amen = selected_amenities - current_amenities
        to_remove_amen = current_amenities - selected_amenities
        to_add_trainers = selected_trainers - current_trainers
        to_remove_trainers = current_trainers - selected_trainers
        to_add_customers = selected_customers - current_customers
        to_remove_customers = current_customers - selected_customers
        with engine.begin() as conn:
            # Update gym fields
            conn.execute(text(
                "UPDATE gyms SET address1=:address1, address2=:address2, city=:city, state=:state, zip=:zip, photo_url=:photo_url "
                "WHERE id = :id"
            ), data)
            # Update amenity mappings
            for amen_id in to_add_amen:
                conn.execute(text(
                    "INSERT INTO gym_amenity_mappings (gym_id, amenity_id) VALUES (:gym, :amen)"
                ), {"gym": gym_id, "amen": amen_id})
            for amen_id in to_remove_amen:
                conn.execute(text(
                    "DELETE FROM gym_amenity_mappings WHERE gym_id = :gym AND amenity_id = :amen"
                ), {"gym": gym_id, "amen": amen_id})
            # Update trainer mappings
            for trainer_id in to_add_trainers:
                conn.execute(text(
                    "INSERT INTO gym_trainer_mappings (gym_id, trainer_id) VALUES (:gym, :trainer)"
                ), {"gym": gym_id, "trainer": trainer_id})
            for trainer_id in to_remove_trainers:
                conn.execute(text(
                    "DELETE FROM gym_trainer_mappings WHERE gym_id = :gym AND trainer_id = :trainer"
                ), {"gym": gym_id, "trainer": trainer_id})
            # Update customer mappings
            for cust_id in to_add_customers:
                conn.execute(text(
                    "INSERT INTO gym_customer_mappings (gym_id, customer_id, created_datetime_utc) "
                    "VALUES (:gym, :cust, now())"
                ), {"gym": gym_id, "cust": cust_id})
            for cust_id in to_remove_customers:
                conn.execute(text(
                    "DELETE FROM gym_customer_mappings WHERE gym_id = :gym AND customer_id = :cust"
                ), {"gym": gym_id, "cust": cust_id})
        return redirect(url_for('gyms.list'))
    # GET: render edit form
    return render_template('gyms/form.html', gym=gym, amenities=amenities, trainers=trainers, customers=customers,
                           selected_amenities=current_amenities, selected_trainers=current_trainers,
                           selected_customers=current_customers)

@bp.route('/<int:gym_id>/delete', methods=['POST'])
def delete(gym_id):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM gyms WHERE id = :id"), {"id": gym_id})
    return redirect(url_for('gyms.list'))

@bp.route('/<int:gym_id>/view')
def view(gym_id):
    with engine.connect() as conn:
        gym = conn.execute(text("SELECT * FROM gyms WHERE id = :id"), {"id": gym_id}).mappings().one_or_none()
        if gym is None:
            return redirect(url_for('gyms.list'))

        # Amenities (with photo)
        amenities = conn.execute(text("""
            SELECT a.name, a.photo_url
            FROM gym_amenity_mappings gam
            JOIN amenities a ON gam.amenity_id = a.id
            WHERE gam.gym_id = :id
        """), {"id": gym_id}).mappings().all()

        # Trainers (full details)
        trainers = conn.execute(text("""
            SELECT t.first_name, t.last_name, t.photo_url, t.certifications, t.years_experience
            FROM gym_trainer_mappings gtm
            JOIN trainers t ON gtm.trainer_id = t.id
            WHERE gtm.gym_id = :id
        """), {"id": gym_id}).mappings().all()

        # Group classes with type and trainer name
        group_classes = conn.execute(text("""
            SELECT gc.class_datetime_utc, gct.name AS class_type_name,
                   t.first_name AS trainer_first_name, t.last_name AS trainer_last_name
            FROM group_classes gc
            LEFT JOIN group_class_types gct ON gc.group_class_type_id = gct.id
            LEFT JOIN trainers t ON gc.trainer_id = t.id
            WHERE gc.gym_id = :id
            ORDER BY gc.class_datetime_utc
        """), {"id": gym_id}).mappings().all()

    return render_template('gyms/view.html',
                           gym=gym,
                           amenities=amenities,
                           trainers=trainers,
                           group_classes=group_classes)