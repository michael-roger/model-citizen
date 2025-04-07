from flask import Blueprint, render_template, request, redirect, url_for
from sqlalchemy import text
from db import engine

bp = Blueprint('membership_types', __name__, url_prefix='/membership_types')

@bp.route('/')
def list():
    with engine.connect() as conn:
        membership_types = conn.execute(text("SELECT * FROM membership_types ORDER BY id ASC")).mappings().all()
    return render_template('membership_types/list.html', membership_types=membership_types)

@bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        data = {
            "name": request.form.get('name', ''),
            "price": request.form.get('price', None),
            "description": request.form.get('description', '')
        }
        with engine.begin() as conn:
            conn.execute(text(
                "INSERT INTO membership_types (name, price, description) VALUES (:name, :price, :description)"
            ), data)
        return redirect(url_for('membership_types.list'))
    return render_template('membership_types/form.html', membership_type=None)

@bp.route('/<int:type_id>/edit', methods=['GET', 'POST'])
def edit(type_id):
    with engine.connect() as conn:
        membership_type = conn.execute(text(
            "SELECT * FROM membership_types WHERE id = :id"
        ), {"id": type_id}).mappings().one_or_none()
        if membership_type is None:
            return redirect(url_for('membership_types.list'))
    if request.method == 'POST':
        data = {
            "id": type_id,
            "name": request.form.get('name', ''),
            "price": request.form.get('price', None),
            "description": request.form.get('description', '')
        }
        with engine.begin() as conn:
            conn.execute(text(
                "UPDATE membership_types SET name=:name, price=:price, description=:description WHERE id = :id"
            ), data)
        return redirect(url_for('membership_types.list'))
    return render_template('membership_types/form.html', membership_type=membership_type)

@bp.route('/<int:type_id>/delete', methods=['POST'])
def delete(type_id):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM membership_types WHERE id = :id"), {"id": type_id})
    return redirect(url_for('membership_types.list'))
