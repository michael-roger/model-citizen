from flask import Flask, render_template

app = Flask(__name__)

# Register Blueprints for each entity
from routes import trainers, gyms, amenities, trainer_specialties, equipment, group_classes, membership_types, \
    customers, group_class_types, membership_purchases

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
