from flask import Blueprint, render_template, request, redirect, url_for
from sqlalchemy import text
from db import engine

bp = Blueprint('membership_purchases', __name__, url_prefix='/membership_purchases')

@bp.route('/')
def list():
    with engine.connect() as conn:
        purchases = conn.execute(text(
            "SELECT mp.id, mp.amount_charged, mp.date_of_membership_start, mp.date_of_membership_end, "
            "mp.membership_type_id, mt.name AS membership_type_name "
            "FROM membership_purchases mp LEFT JOIN membership_types mt ON mp.membership_type_id = mt.id"
        )).mappings().all()
    return render_template('membership_purchases/../templates/membership_purchases/list.html', purchases=purchases)

@bp.route('/add', methods=['GET', 'POST'])
def add():
    with engine.connect() as conn:
        membership_types = conn.execute(text("SELECT id, name FROM membership_types")).mappings().all()
        customers = conn.execute(text("SELECT id, first_name, last_name FROM customers")).mappings().all()
    if request.method == 'POST':
        data = {
            "amount_charged": request.form.get('amount_charged', None),
            "date_of_membership_start": request.form.get('date_of_membership_start', None),
            "date_of_membership_end": request.form.get('date_of_membership_end', None),
            "membership_type_id": request.form.get('membership_type_id', None)
        }
        selected_customers = request.form.getlist('customers')  # customer IDs
        with engine.begin() as conn:
            result = conn.execute(text(
                "INSERT INTO membership_purchases (amount_charged, date_of_membership_start, date_of_membership_end, membership_type_id) "
                "VALUES (:amount_charged, :date_of_membership_start, :date_of_membership_end, :membership_type_id) RETURNING id"
            ), data)
            new_purchase_id = result.scalar_one()
            for cust_id in selected_customers:
                conn.execute(text(
                    "INSERT INTO customer_membership_purchase_mappings (customer_id, membership_purchase_id) "
                    "VALUES (:cust, :mp)"
                ), {"cust": cust_id, "mp": new_purchase_id})
        return redirect(url_for('membership_purchases.list'))
    return render_template('membership_purchases/../templates/membership_purchases/form.html', purchase=None,
                           membership_types=membership_types, customers=customers, selected_customers=[])

@bp.route('/<int:purchase_id>/edit', methods=['GET', 'POST'])
def edit(purchase_id):
    with engine.connect() as conn:
        purchase = conn.execute(text(
            "SELECT * FROM membership_purchases WHERE id = :id"
        ), {"id": purchase_id}).mappings().one_or_none()
        if purchase is None:
            return redirect(url_for('membership_purchases.list'))
        membership_types = conn.execute(text("SELECT id, name FROM membership_types")).mappings().all()
        customers = conn.execute(text("SELECT id, first_name, last_name FROM customers")).mappings().all()
        current_customers = {row['customer_id'] for row in conn.execute(text(
            "SELECT customer_id FROM customer_membership_purchase_mappings WHERE membership_purchase_id = :mp"
        ), {"mp": purchase_id})}
    if request.method == 'POST':
        data = {
            "id": purchase_id,
            "amount_charged": request.form.get('amount_charged', None),
            "date_of_membership_start": request.form.get('date_of_membership_start', None),
            "date_of_membership_end": request.form.get('date_of_membership_end', None),
            "membership_type_id": request.form.get('membership_type_id', None)
        }
        selected_customers = set(request.form.getlist('customers'))
        to_add_customers = selected_customers - current_customers
        to_remove_customers = current_customers - selected_customers
        with engine.begin() as conn:
            conn.execute(text(
                "UPDATE membership_purchases SET amount_charged=:amount_charged, date_of_membership_start=:date_of_membership_start, "
                "date_of_membership_end=:date_of_membership_end, membership_type_id=:membership_type_id WHERE id = :id"
            ), data)
            for cust_id in to_add_customers:
                conn.execute(text(
                    "INSERT INTO customer_membership_purchase_mappings (customer_id, membership_purchase_id) "
                    "VALUES (:cust, :mp)"
                ), {"cust": cust_id, "mp": purchase_id})
            for cust_id in to_remove_customers:
                conn.execute(text(
                    "DELETE FROM customer_membership_purchase_mappings WHERE customer_id = :cust AND membership_purchase_id = :mp"
                ), {"cust": cust_id, "mp": purchase_id})
        return redirect(url_for('membership_purchases.list'))
    return render_template('membership_purchases/../templates/membership_purchases/form.html', purchase=purchase,
                           membership_types=membership_types, customers=customers, selected_customers=current_customers)

@bp.route('/<int:purchase_id>/delete', methods=['POST'])
def delete(purchase_id):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM membership_purchases WHERE id = :id"), {"id": purchase_id})
    return redirect(url_for('membership_purchases.list'))
