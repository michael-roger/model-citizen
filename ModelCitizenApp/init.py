from flask import Flask, render_template
from ModelCitizenApp import db

app = Flask(__name__)

# Initialize database (create tables from schema if needed)
db.init_db()

# Register Blueprints for each entity
from ModelCitizenApp.routes import amenities, customers, equipment, gyms, group_class_types, group_classes, membership_types, membership_purchases, trainer_specialties, trainers

app.register_blueprint(amenities.bp)
app.register_blueprint(customers.bp)
app.register_blueprint(equipment.bp)
app.register_blueprint(gyms.bp)
app.register_blueprint(group_class_types.bp)
app.register_blueprint(group_classes.bp)
app.register_blueprint(membership_types.bp)
app.register_blueprint(membership_purchases.bp)
app.register_blueprint(trainer_specialties.bp)
app.register_blueprint(trainers.bp)

# Home page route
@app.route('/')
def index():
    return render_template('index.html')
