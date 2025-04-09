import os
import jwt
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash
from models.customer import Customer
from extensions import db

admin_signup_bp = Blueprint('admin_signup', __name__)

# Load the admin registration token from environment variable
ADMIN_REGISTRATION_TOKEN = 'admin' 

@admin_signup_bp.route('/admin-signup', methods=['POST', 'OPTIONS'])
def admin_signup():
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'preflight'})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

    try:
        data = request.get_json()
        
        # Validate that all required fields are present
        if not data or not all(key in data for key in ['name', 'email', 'mobile', 'password', 'admin_token']):
            return jsonify({
                'success': False,
                'message': 'All fields are required',
                'required_fields': ['name', 'email', 'mobile', 'password', 'admin_token']
            }), 400
        
        # Debug token verification (remove in production)
        current_app.logger.debug(f"Received token: {data.get('admin_token')}")
        current_app.logger.debug(f"Expected token: {ADMIN_REGISTRATION_TOKEN}")
        
        # Check admin registration token
        if data.get('admin_token') != ADMIN_REGISTRATION_TOKEN:
            return jsonify({
                'success': False,
                'message': 'Invalid admin registration token',
                'hint': 'Check your admin token and try again'
            }), 403
        
        # Validate email format
        if '@' not in data['email'] or '.' not in data['email'].split('@')[-1]:
            return jsonify({
                'success': False,
                'message': 'Invalid email format'
            }), 400

        # Validate mobile number format
        if not data['mobile'].isdigit() or len(data['mobile']) != 10:
            return jsonify({
                'success': False,
                'message': 'Mobile number must be 10 digits'
            }), 400

        # Check for duplicate email or mobile
        if Customer.query.filter_by(email=data['email']).first():
            return jsonify({
                'success': False,
                'message': 'Email already registered',
                'suggestion': 'Try logging in or use a different email'
            }), 400

        if Customer.query.filter_by(mobile=data['mobile']).first():
            return jsonify({
                'success': False,
                'message': 'Mobile number already registered',
                'suggestion': 'Use a different mobile number'
            }), 400

        # Validate password strength
        if len(data['password']) < 8:
            return jsonify({
                'success': False,
                'message': 'Password must be at least 8 characters'
            }), 400

        # Create and save admin customer
        new_admin = Customer(
            name=data['name'].strip(),
            email=data['email'].lower().strip(),
            mobile=data['mobile'].strip(),
            password=generate_password_hash(data['password']),
            role='admin',  # Set role to admin
            # is_verified=True,  
            # created_at=datetime.utcnow()
        )

        db.session.add(new_admin)
        db.session.commit()

        # Generate JWT token
        secret_key = current_app.config['SECRET_KEY']
        payload = {
    'customer_id': new_admin.customer_id,
    'email': new_admin.email,
    'role': new_admin.role,
    'exp': datetime.utcnow() + timedelta(days=1)
}
        token = jwt.encode(payload, secret_key, algorithm='HS256')

        # Prepare response
        response_data = {
            'success': True,
            'message': 'Admin registration successful!',
            'token': token,
            'admin': {
                'customer_id': new_admin.customer_id,
                'name': new_admin.name,
                'email': new_admin.email,
                'mobile': new_admin.mobile,
                'role': new_admin.role,
                # 'is_verified': new_admin.is_verified
            }
        }

        response = jsonify(response_data)
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response, 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Admin registration error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': 'Admin registration failed',
            'error': str(e),
            'hint': 'Check server logs for more details'
        }), 500