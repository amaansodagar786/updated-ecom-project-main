

from flask_login import UserMixin
from extensions import db

class Customer(UserMixin, db.Model):
    __tablename__ = 'customer'
    
    customer_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    mobile = db.Column(db.String(15), unique=True, nullable=True)  # Made nullable for Google users
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    role = db.Column(db.String(20), default='customer')


    
    # Google Auth fields
    google_id = db.Column(db.String(255), unique=True, nullable=True)
    
    # Relationship with OrderHistory
    orders = db.relationship('OrderHistory', backref='customer', lazy=True)
    
    def get_id(self):
        return str(self.customer_id)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_google_user(self):
        return self.google_id is not None