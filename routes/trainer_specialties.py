from flask import Blueprint, render_template, request, redirect, url_for
from sqlalchemy import text
from db import engine

bp = Blueprint('trainer_specialties', __name__, url_prefix='/trainer_specialties')

@bp.route('/')
def list():
    with engine.connect() as conn:
        specialties = conn.execute(text("SELECT * FROM trainer_specialties")).mappings().all()
    return render_template('trainer_specialties/../templates/trainer_specialties/list.html', trainer_specialties=specialties)

@bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        data = {
            "name": request.form.get('name', ''),
            "description": request.form.get('description', '')
        }
        with engine.begin() as conn:
            conn.execute(text(
                "INSERT INTO trainer_specialties (name, description) VALUES (:name, :description)"
            ), data)
        return redirect(url_for('trainer_specialties.list'))
    return render_template('trainer_specialties/../templates/trainer_specialties/form.html', specialty=None)

@bp.route('/<int:specialty_id>/edit', methods=['GET', 'POST'])
def edit(specialty_id):
    with engine.connect() as conn:
        specialty = conn.execute(text(
            "SELECT * FROM trainer_specialties WHERE id = :id"
        ), {"id": specialty_id}).mappings().one_or_none()
        if specialty is None:
            return redirect(url_for('trainer_specialties.list'))
    if request.method == 'POST':
        data = {
            "id": specialty_id,
            "name": request.form.get('name', ''),
            "description": request.form.get('description', '')
        }
        with engine.begin() as conn:
            conn.execute(text(
                "UPDATE trainer_specialties SET name=:name, description=:description WHERE id = :id"
            ), data)
        return redirect(url_for('trainer_specialties.list'))
    return render_template('trainer_specialties/../templates/trainer_specialties/form.html', specialty=specialty)

@bp.route('/<int:specialty_id>/delete', methods=['POST'])
def delete(specialty_id):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM trainer_specialties WHERE id = :id"), {"id": specialty_id})
    return redirect(url_for('trainer_specialties.list'))
