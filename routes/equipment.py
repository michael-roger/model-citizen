from flask import Blueprint, render_template, request, redirect, url_for
from sqlalchemy import text
from db import engine

bp = Blueprint('equipment', __name__, url_prefix='/equipment')

@bp.route('/')
def list():
    # List all equipment with gym info (joining gyms for display)
    with engine.connect() as conn:
        equipment = conn.execute(text(
            "SELECT e.id, e.name, e.serial_number, e.gym_id, g.city AS gym_city "
            "FROM equipment e LEFT JOIN gyms g ON e.gym_id = g.id"
        )).mappings().all()
    return render_template('equipment/equipment/list.html', equipment=equipment)

@bp.route('/add', methods=['GET', 'POST'])
def add():
    # Need list of gyms for the gym dropdown
    with engine.connect() as conn:
        gyms = conn.execute(text("SELECT id, city, state FROM gyms")).mappings().all()
    if request.method == 'POST':
        data = {
            "name": request.form.get('name', ''),
            "photo_url": request.form.get('photo_url', ''),
            "serial_number": request.form.get('serial_number', ''),
            "gym_id": request.form.get('gym_id', None)
        }
        with engine.begin() as conn:
            conn.execute(text(
                "INSERT INTO equipment (name, photo_url, serial_number, gym_id) "
                "VALUES (:name, :photo_url, :serial_number, :gym_id)"
            ), data)
        return redirect(url_for('equipment.list'))
    return render_template('equipment/equipment/form.html', equipment=None, gyms=gyms)

@bp.route('/<int:equipment_id>/edit', methods=['GET', 'POST'])
def edit(equipment_id):
    with engine.connect() as conn:
        equipment = conn.execute(text(
            "SELECT * FROM equipment WHERE id = :id"
        ), {"id": equipment_id}).mappings().one_or_none()
        if equipment is None:
            return redirect(url_for('equipment.list'))
        gyms = conn.execute(text("SELECT id, city, state FROM gyms")).mappings().all()
    if request.method == 'POST':
        data = {
            "id": equipment_id,
            "name": request.form.get('name', ''),
            "photo_url": request.form.get('photo_url', ''),
            "serial_number": request.form.get('serial_number', ''),
            "gym_id": request.form.get('gym_id', None)
        }
        with engine.begin() as conn:
            conn.execute(text(
                "UPDATE equipment SET name=:name, photo_url=:photo_url, serial_number=:serial_number, gym_id=:gym_id "
                "WHERE id = :id"
            ), data)
        return redirect(url_for('equipment.list'))
    return render_template('equipment/equipment/form.html', equipment=equipment, gyms=gyms)

@bp.route('/<int:equipment_id>/delete', methods=['POST'])
def delete(equipment_id):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM equipment WHERE id = :id"), {"id": equipment_id})
    return redirect(url_for('equipment.list'))
