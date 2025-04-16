# from flask import Blueprint, request, jsonify
from flask import Blueprint, request, jsonify, app

from models.offline_customer import OfflineCustomer
from models.address import Address
from extensions import db
from flask_login import login_required, current_user
from middlewares.auth import token_required
from flask_cors import CORS
CORS(app, resources={r"/offline-customers": {"origins": "http://localhost:5173"}})

offline_customer_bp = Blueprint('offline_customer', __name__)

# Create
@offline_customer_bp.route('/offline-customers', methods=['POST'])
@token_required(roles=['admin'])
def create_offline_customer():
    data = request.get_json()
    print("Received data:", data)  # Log incoming data
    
    # Validate required fields
    if not data.get('name') or not data.get('mobile'):
        return jsonify({'message': 'Name and mobile are required'}), 400
    
    try:
        # Create customer
        new_customer = OfflineCustomer(
            name=data['name'],
            mobile=data['mobile'],
            email=data.get('email', ''),
        )
        
        db.session.add(new_customer)
        db.session.flush()  # Get the customer_id before commit
        print("New customer ID:", new_customer.customer_id)  # Log new customer ID
        
        # Add address if provided
        if 'address' in data:
            address_data = data['address']
            print("Address data:", address_data)  # Log address data
            
            # Validate required address fields
            required_address_fields = ['name', 'mobile', 'pincode', 'locality', 'address_line', 'city', 'state_id']
            if not all(field in address_data for field in required_address_fields):
                missing = [f for f in required_address_fields if f not in address_data]
                print("Missing address fields:", missing)
                return jsonify({'message': f'Missing required address fields: {missing}'}), 400
            
            new_address = Address(
                offline_customer_id=new_customer.customer_id,
                name=address_data['name'],
                mobile=address_data['mobile'],
                pincode=address_data['pincode'],
                locality=address_data['locality'],
                address_line=address_data['address_line'],
                city=address_data['city'],
                state_id=address_data['state_id'],
                landmark=address_data.get('landmark', ''),
                alternate_phone=address_data.get('alternate_phone', ''),
                address_type=address_data.get('address_type', 'Home'),
                latitude=address_data.get('latitude'),
                longitude=address_data.get('longitude')
            )
            print("Address object:", new_address)  # Log address object
            db.session.add(new_address)
        
        db.session.commit()
        print("Commit successful")  # Log successful commit
        
        # Prepare response
        customer_dict = {
            'customer_id': new_customer.customer_id,
            'name': new_customer.name,
            'mobile': new_customer.mobile,
            'email': new_customer.email
        }
        
        if 'address' in data:
            customer_dict['address'] = {
                'address_id': new_address.address_id,
                'name': new_address.name,
                'mobile': new_address.mobile,
                'address_line': new_address.address_line,
                'city': new_address.city,
                'state_id': new_address.state_id,
                'pincode': new_address.pincode
            }
            customer_dict['addresses'] = [customer_dict['address']]
        
        return jsonify(customer_dict), 201
    
    except Exception as e:
        db.session.rollback()
        print("Error:", str(e))  # Log the full error
        import traceback
        traceback.print_exc()  # Print full traceback
        return jsonify({
            'message': 'Failed to create customer',
            'error': str(e),
            'type': type(e).__name__
        }), 500



# Read (Get all)
@offline_customer_bp.route('/offline-customers', methods=['GET'])
@token_required(roles=['admin'])
def get_offline_customers():
    customers = OfflineCustomer.query.all()
    result = []
    for customer in customers:
        customer_data = customer.get_dict()
        addresses = [addr.to_dict() for addr in customer.addresses]
        customer_data['addresses'] = addresses
        result.append(customer_data)
    return jsonify(result)

# Read (Get one)
@offline_customer_bp.route('/offline-customers/<int:customer_id>', methods=['GET'])
@token_required(roles=['admin'])
def get_offline_customer(customer_id):
    customer = OfflineCustomer.query.get_or_404(customer_id)
    customer_data = customer.get_dict()
    addresses = [addr.to_dict() for addr in customer.addresses]
    customer_data['addresses'] = addresses
    return jsonify(customer_data)

# Update
@offline_customer_bp.route('/offline-customers/<int:customer_id>', methods=['PUT'])
@token_required(roles=['admin'])
def update_offline_customer(customer_id):
    
        
    customer = OfflineCustomer.query.get_or_404(customer_id)
    data = request.get_json()
    
    customer.name = data.get('name', customer.name)
    customer.mobile = data.get('mobile', customer.mobile)
    customer.email = data.get('email', customer.email)
    customer.age = data.get('age', customer.age)
    customer.gender = data.get('gender', customer.gender)
    
    if 'password' in data:
        customer.password = data['password']
    
    db.session.commit()
    return jsonify(customer.get_dict())

# Delete
@offline_customer_bp.route('/offline-customers/<int:customer_id>', methods=['DELETE'])
@token_required(roles=['admin'])
def delete_offline_customer(customer_id):
    
        
    customer = OfflineCustomer.query.get_or_404(customer_id)
    db.session.delete(customer)
    db.session.commit()
    return jsonify({'message': 'Customer deleted successfully'})

# Add Address
@offline_customer_bp.route('/offline-customers/<int:customer_id>/addresses', methods=['POST'])
@token_required(roles=['admin'])
def add_offline_customer_address(customer_id):
    
        
    customer = OfflineCustomer.query.get_or_404(customer_id)
    data = request.get_json()
    
    new_address = Address(
        offline_customer_id=customer.customer_id,
        street=data['street'],
        city=data['city'],
        state=data['state'],
        pincode=data['pincode'],
        is_default=data.get('is_default', False)
    )
    
    db.session.add(new_address)
    db.session.commit()
    return jsonify({
        'message': 'Address added successfully',
        'address_id': new_address.address_id
    }), 201

# Get Customer Addresses
@offline_customer_bp.route('/offline-customers/<int:customer_id>/addresses', methods=['GET'])
@token_required(roles=['admin'])
def get_offline_customer_addresses(customer_id):
    
        
    customer = OfflineCustomer.query.get_or_404(customer_id)
    addresses = Address.query.filter_by(offline_customer_id=customer.customer_id).all()
    
    return jsonify([{
        'address_id': addr.address_id,
        'street': addr.street,
        'city': addr.city,
        'state': addr.state,
        'pincode': addr.pincode,
        'is_default': addr.is_default
    } for addr in addresses]) 