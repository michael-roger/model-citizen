from flask import Blueprint, render_template, request, redirect, url_for
from sqlalchemy import text
from db import engine

bp = Blueprint('amenities', __name__, url_prefix='/amenities')

@bp.route('/')
def list():
    # List all amenities
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, name, photo_url FROM amenities"))
        amenities = result.mappings().all()
    return render_template('amenities/amenities/list.html', amenities=amenities)

@bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        name = request.form.get('name', '')
        photo_url = request.form.get('photo_url', '')
        # Insert new amenity into DB
        with engine.begin() as conn:
            conn.execute(text(
                "INSERT INTO amenities (name, photo_url) VALUES (:name, :photo)"
            ), {"name": name, "photo": photo_url})
        return redirect(url_for('amenities.list'))
    # GET: display empty form
    return render_template('amenities/amenities/form.html', amenity=None)

@bp.route('/<int:amenity_id>/edit', methods=['GET', 'POST'])
def edit(amenity_id):
    # Fetch the amenity to edit
    with engine.connect() as conn:
        amenity = conn.execute(text(
            "SELECT id, name, photo_url FROM amenities WHERE id = :id"
        ), {"id": amenity_id}).mappings().one_or_none()
    if amenity is None:
        return redirect(url_for('amenities.list'))
    if request.method == 'POST':
        name = request.form.get('name', '')
        photo_url = request.form.get('photo_url', '')
        with engine.begin() as conn:
            conn.execute(text(
                "UPDATE amenities SET name = :name, photo_url = :photo WHERE id = :id"
            ), {"name": name, "photo": photo_url, "id": amenity_id})
        return redirect(url_for('amenities.list'))
    # GET: display form with current amenity data
    return render_template('amenities/amenities/form.html', amenity=amenity)

@bp.route('/<int:amenity_id>/delete', methods=['POST'])
def delete(amenity_id):
    # Delete amenity (will error if mappings exist, see note above)
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM amenities WHERE id = :id"), {"id": amenity_id})
    return redirect(url_for('amenities.list'))
