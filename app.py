# app.py
from flask import Flask, jsonify
from flask_cors import CORS
from datetime import timedelta
from extensions import db
from routes.signup import signup_bp
from routes.login import login_bp, setup_google_oauth
from routes.products import products_bp
from routes.order import order_bp
from routes.admin_signup import admin_signup_bp
from routes.wishlist import wishlist_bp

# Import models
from models.customer import Customer
from models.product import Product, ProductImage
from models.order import OrderHistory, OrderHistoryItem
from models.cart import Cart, CartItem
from flask import Flask, jsonify, send_from_directory


import os
import secrets

# Initialize Flask app
# app = Flask(__name__)
app = Flask(__name__, static_folder='static')

client_id = os.getenv("GOOGLE_CLIENT_ID")
client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
# Generate a secure secret key
# app.config['SECRET_KEY'] = secrets.token_hex(32)

# app.config['SECRET_KEY'] = "shrivarajunizationfaranfusion"

# Google OAuth configuration
app.config['GOOGLE_CLIENT_ID'] = client_id  # Replace with your Google Client ID
app.config['GOOGLE_CLIENT_SECRET'] = client_secret # Replace with your Google Client Secret


# Remove any duplicate static route definitions and use this:
@app.route('/product_images/<filename>')
def serve_product_image(filename):
    return send_from_directory(os.path.join(app.static_folder, 'product_images'), filename)




app.config['SECRET_KEY'] = secrets.token_hex(32)

# Remove session-related configurations
# Remove Flask-Session initialization

# Enable CORS with enhanced security
# Enable CORS with enhanced security for both ports
# Replace your current CORS config with this:
cors = CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:5173", "http://localhost:5174"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True,
        "expose_headers": ["Authorization"]
    }
})


# Configure MySQL database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost/ecom-project'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Security configurations
app.config['JWT_SECRET_KEY'] = secrets.token_hex(32)
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)

# Initialize extensions
db.init_app(app)

# Initialize Google OAuth
setup_google_oauth(app)

# Register blueprints
app.register_blueprint(signup_bp)
app.register_blueprint(login_bp)
app.register_blueprint(products_bp)
app.register_blueprint(order_bp)
app.register_blueprint(admin_signup_bp)
app.register_blueprint(wishlist_bp)

@app.after_request
def add_security_headers(response):
    """Add additional security headers"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    # CORS headers
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:5173"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    
    return response

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        'message': 'Unauthorized access',
        'status': 'error'
    }), 401


# ✅ Fix for Home Route
@app.route('/')
def home():
    return "Hello, World!"


if __name__ == '__main__':
    # Ensure database tables are created
    with app.app_context():
        db.create_all()
    



    # Run the app
    app.run(debug=True)