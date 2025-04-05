from datetime import datetime, UTC
from extensions import db

class OrderHistory(db.Model):
    __tablename__ = 'orderhistory'
    
    order_id = db.Column(db.Integer, primary_key=True , autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.customer_id'))
    address = db.Column(db.Text , nullable=True)
    date_time = db.Column(db.DateTime, default=lambda: datetime.now(UTC) , nullable=True)
    num_products = db.Column(db.Integer , default=0)
    total_price = db.Column(db.Numeric(10, 2) , default=0)
    delivery_charge = db.Column(db.Numeric(10, 2) , default=0)
    final_payment = db.Column(db.Numeric(10, 2) , default=0)
    status = db.Column(db.Text,default="PENDING")
    
    # Relationship with OrderHistoryItem
    items = db.relationship('OrderHistoryItem', backref='order', lazy=True)

class OrderHistoryItem(db.Model):
    __tablename__ = 'orderhistoryitems'
    
    item_id = db.Column(db.Integer, primary_key=True , autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orderhistory.order_id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'))
    quantity = db.Column(db.Integer)
    product_price = db.Column(db.Numeric(10, 2)) 