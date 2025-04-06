from flask import Blueprint, render_template, request, redirect, url_for
from sqlalchemy import text
from db import engine

bp = Blueprint('trainers', __name__, url_prefix='/trainers')

@bp.route('/')
def list():
    # List all trainers (a few fields for brevity)
    with engine.connect() as conn:
        trainers = conn.execute(text(
            "SELECT id, first_name, last_name, job_title, years_experience FROM trainers"
        )).mappings().all()
    return render_template('trainers/list.html', trainers=trainers)

@bp.route('/add', methods=['GET', 'POST'])
def add():
    with engine.connect() as conn:
        gyms = conn.execute(text("SELECT id, city, state FROM gyms")).mappings().all()
        specialties = conn.execute(text("SELECT id, name FROM trainer_specialties")).mappings().all()
    if request.method == 'POST':
        data = {
            "first_name": request.form.get('first_name', ''),
            "last_name": request.form.get('last_name', ''),
            "date_of_hire": request.form.get('date_of_hire', None),
            "date_of_termination": request.form.get('date_of_termination', None),
            "date_of_birth": request.form.get('date_of_birth', None),
            "job_title": request.form.get('job_title', ''),
            "photo_url": request.form.get('photo_url', ''),
            "certifications": request.form.get('certifications', ''),
            "years_experience": request.form.get('years_experience', None)
        }
        selected_gyms = request.form.getlist('gyms')            # gym IDs
        selected_specialties = request.form.getlist('specialties')  # specialty IDs
        with engine.begin() as conn:
            result = conn.execute(text(
                "INSERT INTO trainers (first_name, last_name, date_of_hire, date_of_termination, date_of_birth, job_title, photo_url, certifications, years_experience) "
                "VALUES (:first_name, :last_name, :date_of_hire, :date_of_termination, :date_of_birth, :job_title, :photo_url, :certifications, :years_experience) RETURNING id"
            ), data)
            new_trainer_id = result.scalar_one()
            for gym_id in selected_gyms:
                conn.execute(text(
                    "INSERT INTO gym_trainer_mappings (gym_id, trainer_id) VALUES (:gym, :trainer)"
                ), {"gym": gym_id, "trainer": new_trainer_id})
            for spec_id in selected_specialties:
                conn.execute(text(
                    "INSERT INTO trainer_trainer_specialty_mappings (trainer_id, trainer_specialty_id) VALUES (:trainer, :spec)"
                ), {"trainer": new_trainer_id, "spec": spec_id})
        return redirect(url_for('trainers.list'))
    return render_template('trainers/form.html', trainer=None, gyms=gyms, specialties=specialties,
                           selected_gyms=[], selected_specialties=[])

@bp.route('/<int:trainer_id>/edit', methods=['GET', 'POST'])
def edit(trainer_id):
    with engine.connect() as conn:
        trainer = conn.execute(text("SELECT * FROM trainers WHERE id = :id"), {"id": trainer_id}) \
            .mappings().one_or_none()
        if trainer is None:
            return redirect(url_for('trainers.list'))
        gyms = conn.execute(text("SELECT id, city, state FROM gyms")).mappings().all()
        specialties = conn.execute(text("SELECT id, name FROM trainer_specialties")).mappings().all()
        current_gyms = {row['gym_id'] for row in conn.execute(text(
            "SELECT gym_id FROM gym_trainer_mappings WHERE trainer_id = :trainer"
        ), {"trainer": trainer_id})}
        current_specialties = {row['trainer_specialty_id'] for row in conn.execute(text(
            "SELECT trainer_specialty_id FROM trainer_trainer_specialty_mappings WHERE trainer_id = :trainer"
        ), {"trainer": trainer_id})}
    if request.method == 'POST':
        data = {
            "id": trainer_id,
            "first_name": request.form.get('first_name', ''),
            "last_name": request.form.get('last_name', ''),
            "date_of_hire": request.form.get('date_of_hire', None),
            "date_of_termination": request.form.get('date_of_termination', None),
            "date_of_birth": request.form.get('date_of_birth', None),
            "job_title": request.form.get('job_title', ''),
            "photo_url": request.form.get('photo_url', ''),
            "certifications": request.form.get('certifications', ''),
            "years_experience": request.form.get('years_experience', None)
        }
        selected_gyms = set(request.form.getlist('gyms'))
        selected_specialties = set(request.form.getlist('specialties'))
        to_add_gyms = selected_gyms - current_gyms
        to_remove_gyms = current_gyms - selected_gyms
        to_add_specs = selected_specialties - current_specialties
        to_remove_specs = current_specialties - selected_specialties
        with engine.begin() as conn:
            conn.execute(text(
                "UPDATE trainers SET first_name=:first_name, last_name=:last_name, date_of_hire=:date_of_hire, "
                "date_of_termination=:date_of_termination, date_of_birth=:date_of_birth, job_title=:job_title, "
                "photo_url=:photo_url, certifications=:certifications, years_experience=:years_experience WHERE id = :id"
            ), data)
            for gym_id in to_add_gyms:
                conn.execute(text(
                    "INSERT INTO gym_trainer_mappings (gym_id, trainer_id) VALUES (:gym, :trainer)"
                ), {"gym": gym_id, "trainer": trainer_id})
            for gym_id in to_remove_gyms:
                conn.execute(text(
                    "DELETE FROM gym_trainer_mappings WHERE gym_id = :gym AND trainer_id = :trainer"
                ), {"gym": gym_id, "trainer": trainer_id})
            for spec_id in to_add_specs:
                conn.execute(text(
                    "INSERT INTO trainer_trainer_specialty_mappings (trainer_id, trainer_specialty_id) VALUES (:trainer, :spec)"
                ), {"trainer": trainer_id, "spec": spec_id})
            for spec_id in to_remove_specs:
                conn.execute(text(
                    "DELETE FROM trainer_trainer_specialty_mappings WHERE trainer_id = :trainer AND trainer_specialty_id = :spec"
                ), {"trainer": trainer_id, "spec": spec_id})
        return redirect(url_for('trainers.list'))
    return render_template('trainers/form.html', trainer=trainer, gyms=gyms, specialties=specialties,
                           selected_gyms=current_gyms, selected_specialties=current_specialties)

@bp.route('/<int:trainer_id>/delete', methods=['POST'])
def delete(trainer_id):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM trainers WHERE id = :id"), {"id": trainer_id})
    return redirect(url_for('trainers.list'))
