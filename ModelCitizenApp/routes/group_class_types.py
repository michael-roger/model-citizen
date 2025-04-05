from flask import Blueprint, render_template, request, redirect, url_for
from sqlalchemy import text
from ModelCitizenApp.db import engine

bp = Blueprint('group_class_types', __name__, url_prefix='/group_class_types')

@bp.route('/')
def list():
    with engine.connect() as conn:
        types = conn.execute(text("SELECT * FROM group_class_types")).mappings().all()
    return render_template('group_class_types/list.html', group_class_types=types)

@bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        data = {
            "name": request.form.get('name', ''),
            "photo_url": request.form.get('photo_url', '')
        }
        with engine.begin() as conn:
            conn.execute(text(
                "INSERT INTO group_class_types (name, photo_url) VALUES (:name, :photo_url)"
            ), data)
        return redirect(url_for('group_class_types.list'))
    return render_template('group_class_types/form.html', group_class_type=None)

@bp.route('/<int:type_id>/edit', methods=['GET', 'POST'])
def edit(type_id):
    with engine.connect() as conn:
        group_class_type = conn.execute(text(
            "SELECT * FROM group_class_types WHERE id = :id"
        ), {"id": type_id}).mappings().one_or_none()
        if group_class_type is None:
            return redirect(url_for('group_class_types.list'))
    if request.method == 'POST':
        data = {
            "id": type_id,
            "name": request.form.get('name', ''),
            "photo_url": request.form.get('photo_url', '')
        }
        with engine.begin() as conn:
            conn.execute(text(
                "UPDATE group_class_types SET name=:name, photo_url=:photo_url WHERE id = :id"
            ), data)
        return redirect(url_for('group_class_types.list'))
    return render_template('group_class_types/form.html', group_class_type=group_class_type)

@bp.route('/<int:type_id>/delete', methods=['POST'])
def delete(type_id):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM group_class_types WHERE id = :id"), {"id": type_id})
    return redirect(url_for('group_class_types.list'))
