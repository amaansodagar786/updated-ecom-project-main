# NEW 
import os
from venv import logger
from flask import Blueprint, request, jsonify, session
from werkzeug.utils import secure_filename
from extensions import db
from models.cart import Cart,CartItem
from models.wishlist import Wishlist,WishlistItem
from models.product import Product, ProductImage, ProductModel, ProductColor, ModelSpecification , ProductSpecification
from models.category import Category, Subcategory
from models.hsn import HSN
from uuid import uuid4
from middlewares.auth import token_required
from datetime import datetime
import json
from sqlalchemy import func # new added
from urllib.parse import unquote




products_bp = Blueprint('products', __name__)

# List all products with their images and categories
@products_bp.route('/products', methods=['GET'])
def list_products(): 
    try:
        products = Product.query.options(
            db.joinedload(Product.images),
            db.joinedload(Product.main_category),
            db.joinedload(Product.sub_category),
            db.joinedload(Product.specifications),
            db.joinedload(Product.models).joinedload(ProductModel.specifications),
            db.joinedload(Product.colors).joinedload(ProductColor.images),
            db.joinedload(Product.hsn),
        ).all()
        
        products_list = []
        for product in products:
            product_dict = {
                'product_id': product.product_id,
                'name': product.name,
                'description': product.description,
                'category': product.main_category.name if product.main_category else None,
                'subcategory': product.sub_category.name if product.sub_category else None,
                'hsn': product.hsn.hsn_code if product.hsn else None,
                'sku_id': product.sku_id,                
                'product_type': product.product_type,
                'rating': product.rating,  # Average rating
                'offers': product.offers,
                'raters': product.raters,  # Total number of raters
                'images': [{'image_id': img.image_id, 'image_url': img.image_url} for img in product.images],
                'specifications': [{'spec_id': s.spec_id, 'key': s.key, 'value': s.value} for s in product.specifications],
            }
            
            # Add models for all product types
            product_dict['models'] = []
            
            for model in product.models:
                model_dict = {
                    'model_id': model.model_id,
                    'name': model.name,
                    'description': model.description,
                    'colors': [],
                    'specifications': [
                        {'spec_id': spec.spec_id , 'key': spec.key, 'value': spec.value} for spec in model.specifications
                    ]
                }
                
                for color in model.colors:
                    color_dict = {
                        'color_id': color.color_id,
                        'name': color.name,
                        'stock_quantity': color.stock_quantity,
                        'price': float(color.price),
                        'original_price': float(color.original_price) if color.original_price else None,
                        'threshold': color.threshold,
                        'images': [{'image_id': img.image_id, 'image_url': img.image_url} for img in color.images]
                    }
                    model_dict['colors'].append(color_dict)
                
                product_dict['models'].append(model_dict)
            
            # Add single product specific info
            if product.product_type == 'single':
                product_dict['colors'] = []
                
                for color in product.colors:
                    color_dict = {
                        'color_id': color.color_id,
                        'name': color.name,
                        'stock_quantity': color.stock_quantity,
                        'price': float(color.price),
                        'original_price': float(color.original_price) if color.original_price else None,
                        'threshold': color.threshold,
                        'images': [{'image_id': img.image_id, 'image_url': img.image_url} for img in color.images]
                    }
                    product_dict['colors'].append(color_dict)
            
            products_list.append(product_dict)

        return jsonify(products_list)

    except Exception as e:
        logger.error(f"Error listing products: {str(e)}")
        return jsonify({'error': str(e)}), 500



# Get product details by product_id
@products_bp.route('/product/<int:product_id>', methods=['GET'])
def product_detail(product_id):
    try:
        product = Product.query.options(
            db.joinedload(Product.images),
            db.joinedload(Product.main_category),
            db.joinedload(Product.sub_category),
            db.joinedload(Product.hsn),
            db.joinedload(Product.models).joinedload(ProductModel.colors).joinedload(ProductColor.images),
            db.joinedload(Product.models).joinedload(ProductModel.specifications),
            db.joinedload(Product.colors).joinedload(ProductColor.images)
        ).get_or_404(product_id)

        product_dict = {
            'product_id': product.product_id,
            'name': product.name,
            'description': product.description,
            'category': product.main_category.name if product.main_category else None,
            'subcategory': product.sub_category.name if product.sub_category else None,
            'hsn_id': product.hsn.hsn_code if product.hsn else None,
            'sku_id': product.sku_id,
            'product_type': product.product_type,
            'rating': product.rating,  # Average rating
            'raters': product.raters,  # Total number of raters
            'offers': product.offers,
            'images': [{'image_id': img.image_id, 'image_url': img.image_url} for img in product.images],
            'specifications': [{'spec_id': s.spec_id, 'key': s.key, 'value': s.value} for s in product.specifications],
        }
        
        # Add models for all product types
        product_dict['models'] = []
        
        for model in product.models:
            model_dict = {
                'model_id': model.model_id,
                'name': model.name,
                'description': model.description,
                'colors': [],
                'specifications': [{'spec_id': s.spec_id, 'key': s.key, 'value': s.value} for s in product.specifications],
            }
            
            for color in model.colors:
                color_dict = {
                    'color_id': color.color_id,
                    'name': color.name,
                    'stock_quantity': color.stock_quantity,
                    'price': float(color.price),
                    'original_price': float(color.original_price) if color.original_price else None,
                    'threshold': color.threshold,
                    'images': [{'image_id': img.image_id, 'image_url': img.image_url} for img in color.images]
                }
                model_dict['colors'].append(color_dict)
            
            product_dict['models'].append(model_dict)
        
        # Add single product specific info
        if product.product_type == 'single':
            product_dict['colors'] = []
            
            for color in product.colors:
                color_dict = {
                    'color_id': color.color_id,
                    'name': color.name,
                    'stock_quantity': color.stock_quantity,
                    'price': float(color.price),
                    'original_price': float(color.original_price) if color.original_price else None,
                    'threshold': color.threshold,
                    'images': [{'image_id': img.image_id, 'image_url': img.image_url} for img in color.images]
                }
                product_dict['colors'].append(color_dict)
        
        return jsonify(product_dict)
    
    except Exception as e:
        logger.error(f"Error getting product details: {str(e)}")
        return jsonify({'error': str(e)}), 500


@products_bp.route('/product/slug/<product_slug>', methods=['GET'])
def get_product_by_slug(product_slug):
    try:
        # First try to find by ID if slug is numeric
        if product_slug.isdigit():
            product = Product.query.options(
                db.joinedload(Product.images),
                db.joinedload(Product.main_category),
                db.joinedload(Product.sub_category),
                db.joinedload(Product.hsn),
                db.joinedload(Product.models).joinedload(ProductModel.colors).joinedload(ProductColor.images),
                db.joinedload(Product.models).joinedload(ProductModel.specifications),
                db.joinedload(Product.colors).joinedload(ProductColor.images)
            ).get(product_slug)
            if product:
                product_dict = {
                    'product_id': product.product_id,
                    'name': product.name,
                    'description': product.description,
                    'category': getattr(product.main_category, 'name', None),
                    'subcategory': getattr(product.sub_category, 'name', None),
                    'hsn_id': getattr(getattr(product, 'hsn', None), 'hsn_code', None),
                    'product_type': product.product_type,
                    'rating': product.rating,  # Average rating
                    'raters': product.raters,  # Total number of raters
                    'offers': product.offers,
                    'images': [{'image_id': img.image_id, 'image_url': img.image_url} for img in product.images],
                    'specifications': [{'spec_id': s.spec_id, 'key': s.key, 'value': s.value} for s in product.specifications],
                    'models': [],
                    'colors': []
                }
                
                # Add models data if exists
                for model in product.models:
                    model_dict = {
                        'model_id': model.model_id,
                        'name': model.name,
                        'description': model.description,
                        'colors': [],
                        'specifications': [{'spec_id': s.spec_id, 'key': s.key, 'value': s.value} for s in model.specifications]
                    }
                    
                    for color in model.colors:
                        color_dict = {
                            'color_id': color.color_id,
                            'name': color.name,
                            'stock_quantity': color.stock_quantity,
                            'price': float(color.price),
                            'original_price': float(color.original_price) if color.original_price else None,
                            'threshold': color.threshold,
                            'images': [{'image_id': img.image_id, 'image_url': img.image_url} for img in color.images]
                        }
                        model_dict['colors'].append(color_dict)
                    
                    product_dict['models'].append(model_dict)
                
                # Add colors for single product type
                if product.product_type == 'single':
                    for color in product.colors:
                        color_dict = {
                            'color_id': color.color_id,
                            'name': color.name,
                            'stock_quantity': color.stock_quantity,
                            'price': float(color.price),
                            'original_price': float(color.original_price) if color.original_price else None,
                            'threshold': color.threshold,
                            'images': [{'image_id': img.image_id, 'image_url': img.image_url} for img in color.images]
                        }
                        product_dict['colors'].append(color_dict)
                
                return jsonify(product_dict)
        
        # Otherwise search by name (with hyphens replaced by spaces)
        name = unquote(product_slug).replace('-', ' ')
        product = Product.query.options(
            db.joinedload(Product.images),
            db.joinedload(Product.main_category),
            db.joinedload(Product.sub_category),
            db.joinedload(Product.hsn),
            db.joinedload(Product.models).joinedload(ProductModel.colors).joinedload(ProductColor.images),
            db.joinedload(Product.models).joinedload(ProductModel.specifications),
            db.joinedload(Product.colors).joinedload(ProductColor.images)
        ).filter(
            func.replace(Product.name, '-', ' ').ilike(f'%{name}%')
        ).first()
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        product_dict = {
            'product_id': product.product_id,
            'name': product.name,
            'description': product.description,
            'category': getattr(product.main_category, 'name', None),
            'subcategory': getattr(product.sub_category, 'name', None),
            'hsn_id': getattr(getattr(product, 'hsn', None), 'hsn_code', None),
            'product_type': product.product_type,
            'rating': product.rating,  # Average rating
            'raters': product.raters,  # Total number of raters
            'offers': product.offers,
            'images': [{'image_id': img.image_id, 'image_url': img.image_url} for img in product.images],
            'specifications': [{'spec_id': s.spec_id, 'key': s.key, 'value': s.value} for s in product.specifications],
            'models': [],
            'colors': []
        }
        
        # Add models data if exists
        for model in product.models:
            model_dict = {
                'model_id': model.model_id,
                'name': model.name,
                'description': model.description,
                'colors': [],
                'specifications': [{'spec_id': s.spec_id, 'key': s.key, 'value': s.value} for s in model.specifications]
            }
            
            for color in model.colors:
                color_dict = {
                    'color_id': color.color_id,
                    'name': color.name,
                    'stock_quantity': color.stock_quantity,
                    'price': float(color.price),
                    'original_price': float(color.original_price) if color.original_price else None,
                    'threshold': color.threshold,
                    'images': [{'image_id': img.image_id, 'image_url': img.image_url} for img in color.images]
                }
                model_dict['colors'].append(color_dict)
            
            product_dict['models'].append(model_dict)
        
        # Add colors for single product type
        if product.product_type == 'single':
            for color in product.colors:
                color_dict = {
                    'color_id': color.color_id,
                    'name': color.name,
                    'stock_quantity': color.stock_quantity,
                    'price': float(color.price),
                    'original_price': float(color.original_price) if color.original_price else None,
                    'threshold': color.threshold,
                    'images': [{'image_id': img.image_id, 'image_url': img.image_url} for img in color.images]
                }
                product_dict['colors'].append(color_dict)
        
        return jsonify(product_dict)
        
    except Exception as e:
        logger.error(f"Error getting product by slug {product_slug}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    


@products_bp.route('/product/<int:product_id>/similar', methods=['GET'])
def get_similar_products(product_id):
    try:
        current_product = Product.query.options(
            db.joinedload(Product.main_category),
            db.joinedload(Product.sub_category),
            db.joinedload(Product.colors),
            db.joinedload(Product.models).joinedload(ProductModel.colors)
        ).get_or_404(product_id)
        
        if not current_product.main_category:
            return jsonify({'similar_products': []})
        
        similar_products = Product.query.filter(
            Product.product_id != product_id,
            Product.main_category.has(category_id=current_product.main_category.category_id),
            Product.product_type == current_product.product_type
        ).options(
            db.joinedload(Product.images),
            db.joinedload(Product.main_category),
            db.joinedload(Product.sub_category),
            db.joinedload(Product.colors),
            db.joinedload(Product.models).joinedload(ProductModel.colors)
        ).limit(8).all()
        
        result = []
        for product in similar_products:
            # Get price info using same logic as frontend
            price_info = get_product_price_info(product)
            
            product_dict = {
                'product_id': product.product_id,
                'name': product.name,
                'description': product.description,
                'category': product.main_category.name if product.main_category else None,
                'product_type': product.product_type,
                'rating': product.rating,
                'raters': product.raters,
                'images': [{
                    'image_url': img.image_url,
                    'is_video': img.image_url.lower().endswith('.mp4')
                } for img in product.images],
                'price': price_info['price'],
                'original_price': price_info['original_price'],
                'stock_quantity': price_info['stock_quantity'],
                'colors': [{
                    'color_id': c.color_id,
                    'name': c.name,
                    'price': float(c.price) if c.price else None,
                    'original_price': float(c.original_price) if c.original_price else None,
                    'stock_quantity': c.stock_quantity
                } for c in product.colors] if product.product_type == 'single' else None,
                'models': [{
                    'model_id': m.model_id,
                    'name': m.name,
                    'description': m.description,
                    'colors': [{
                        'color_id': c.color_id,
                        'name': c.name,
                        'price': float(c.price) if c.price else None,
                        'original_price': float(c.original_price) if c.original_price else None,
                        'stock_quantity': c.stock_quantity
                    } for c in m.colors]
                } for m in product.models] if product.product_type == 'variable' else None
            }
            
            result.append(product_dict)
        
        return jsonify({'similar_products': result})
    
    except Exception as e:
        logger.error(f"Error getting similar products: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

def get_product_price_info(product):
    """Helper function to calculate price info same as frontend logic"""
    price = None
    original_price = None
    stock_quantity = 0
    
    if product.product_type == 'single' and product.colors:
        valid_colors = [c for c in product.colors if c.price is not None]
        if valid_colors:
            min_price_color = min(valid_colors, key=lambda x: x.price)
            price = float(min_price_color.price)
            if min_price_color.original_price:
                original_price = float(min_price_color.original_price)
            stock_quantity = sum(c.stock_quantity for c in product.colors)
    
    elif product.product_type == 'variable' and product.models:
        all_colors = []
        for model in product.models:
            if model.colors:
                all_colors.extend(model.colors)
        
        valid_colors = [c for c in all_colors if c.price is not None]
        if valid_colors:
            min_price_color = min(valid_colors, key=lambda x: x.price)
            price = float(min_price_color.price)
            if min_price_color.original_price:
                original_price = float(min_price_color.original_price)
            stock_quantity = sum(c.stock_quantity for c in all_colors)
    
    return {
        'price': price,
        'original_price': original_price,
        'stock_quantity': stock_quantity
    }




@products_bp.route('/offers/update', methods=['POST'])
def update_offer():
    try:
        data = request.get_json()
        print("Received data:", data)  # ✅ Debug log

        product_id = data.get('product_id')
        offer_value = data.get('offer_value')
        print(f"Parsed product_id: {product_id}, offer_value: {offer_value}")  # ✅ Debug log

        if not product_id:
            print("Error: Product ID is missing")  # ✅ Debug log
            return jsonify({'error': 'Product ID is required'}), 400

        # Validate offer value (either None or between 0-100)
        if offer_value is not None:
            try:
                offer_value = int(offer_value)
                if offer_value < 0 or offer_value > 100:
                    print("Error: Offer out of range")  # ✅ Debug log
                    return jsonify({'error': 'Offer must be between 0 and 100'}), 400
            except ValueError:
                print("Error: Offer is not a valid integer")  # ✅ Debug log
                return jsonify({'error': 'Invalid offer value'}), 400

        product = Product.query.get(product_id)
        if not product:
            print(f"Error: Product with ID {product_id} not found")  # ✅ Debug log
            return jsonify({'error': 'Product not found'}), 404

        # Update the offer
        product.offers = str(offer_value) if offer_value is not None else None
        product.updated_at = datetime.utcnow()
        db.session.commit()

        print(f"Offer updated: Product ID {product_id}, New offer: {product.offers}")  # ✅ Debug log

        return jsonify({
            'message': 'Offer updated successfully',
            'product_id': product.product_id,
            'offers': product.offers
        }), 200

    except Exception as e:
        db.session.rollback()
        print("Exception occurred:", str(e))  # ✅ Debug log
        return jsonify({'error': str(e)}), 500



# Routes for categories
@products_bp.route('/categories', methods=['GET'])
def get_categories():
    try:
        categories = Category.query.all()
        result = []
        
        for category in categories:
            cat_dict = {
                'category_id': category.category_id,
                'name': category.name,
                'image_url':category.image_url,
                'subcategories': []
            }
            
            for subcategory in category.subcategories:
                cat_dict['subcategories'].append({
                    'subcategory_id': subcategory.subcategory_id,
                    'name': subcategory.name
                })
            
            result.append(cat_dict)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting categories: {str(e)}")
        return jsonify({'error': str(e)}), 500



# ROUTE FOR HSN 
@products_bp.route('/hsn', methods=['GET'])
def get_hsn():
    try:
        hsn_list = HSN.query.all()
        result = []
        
        for hsn in hsn_list:
            result.append({
                'hsn_id': hsn.hsn_id,
                'hsn_code': hsn.hsn_code if hsn else None,
                'description': hsn.hsn_description  # Corrected field name

            })
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting HSN: {str(e)}")
        return jsonify({'error': str(e)}), 500



UPLOAD_FOLDER = 'static/product_images'
ALLOWED_EXTENSIONS = {
    'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'tif', 'webp',
    'svg', 'ico', 'heif', 'heic', 'raw', 'psd', 'ai', 'eps', 'jfif',
    'avif' , 'mp4'
}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(image_file):
    if image_file and allowed_file(image_file.filename):
        # Generate unique filename
        filename = f"{uuid4().hex}_{secure_filename(image_file.filename)}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        # Save file
        image_file.save(file_path)
        return f'/product_images/{filename}'
    return None



@products_bp.route('/product/add', methods=['POST'])
@token_required(roles=['admin'])
def add_product():
    # Ensure upload directory exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    try:
        # Extract basic product information
        name = request.form.get('name')
        description = request.form.get('description')
        product_type = request.form.get('product_type')

        # Handle category, subcategory, and hsn
        category_id = request.form.get('category_id')
        subcategory_id = request.form.get('subcategory_id')
        hsn_id = request.form.get('hsn_id')

        # Check if we need to create a new category
        if not category_id and request.form.get('new_category'):
            new_category = Category(
                name=request.form.get('new_category'),
                image_url=save_image(request.files.get('image'))
            )
            db.session.add(new_category)
            db.session.commit()
            category_id = new_category.category_id

        # Check if we need to create a new subcategory
        if category_id and not subcategory_id and request.form.get('new_subcategory'):
            new_subcategory = Subcategory(
                name=request.form.get('new_subcategory'),
                category_id=category_id
            )
            db.session.add(new_subcategory)
            db.session.commit()
            subcategory_id = new_subcategory.subcategory_id

        # Check if we need to create a new HSN
        if not hsn_id and request.form.get('new_hsn_code'):
            new_hsn = HSN(
                hsn_code=request.form.get('new_hsn_code'),
                hsn_description=request.form.get('new_hsn_description', '')
            )
            db.session.add(new_hsn)
            db.session.commit()
            hsn_id = new_hsn.hsn_id

        # Validate required fields
        print(name, description, category_id, product_type)
        if not all([name, description, category_id, product_type]):
            return jsonify({'message': 'Missing required product details'}), 400

        # Create new product
        new_product = Product(
            name=name,
            description=description,
            category_id=category_id,
            subcategory_id=subcategory_id,
            hsn_id=hsn_id,
            product_type=product_type,
            rating=0,
            raters=0
        )
        db.session.add(new_product)
        db.session.commit()

        # Handle product-level images
        product_images = request.files.getlist('product_images')
        for image_file in product_images:
            image_url = save_image(image_file)
            if image_url:
                product_image = ProductImage(
                    product_id=new_product.product_id,
                    image_url=image_url
                )
                db.session.add(product_image)

        # Handle Single Product
        if product_type == 'single':
            # Get model name and description from new fields, fallback to product values if not provided
            model_name = request.form.get('model_name', name)
            model_description = request.form.get('model_description', description)
            
            # Create default model for single product with specific model name and description
            default_model = ProductModel(
                product_id=new_product.product_id,
                name=model_name,
                description=model_description
            )
            db.session.add(default_model)
            db.session.commit()

            # Process specifications
            specs_count = int(request.form.get('specs_count', 0))
            for i in range(specs_count):
                spec_key = request.form.get(f'spec_key_{i}')
                spec_value = request.form.get(f'spec_value_{i}')
                if spec_key and spec_value:
                    spec = ProductSpecification(
                        product_id=new_product.product_id,
                        key=spec_key,
                        value=spec_value
                    )
                    db.session.add(spec)

            # Process colors
            colors_count = int(request.form.get('colors_count', 0))
            for i in range(colors_count):
                color_name = request.form.get(f'color_name_{i}')
                color_price = request.form.get(f'color_price_{i}')
                color_original_price = request.form.get(f'color_original_price_{i}')
                color_stock = request.form.get(f'color_stock_{i}', 0)
                threshold = request.form.get(f'threshold_{i}', 10)

                if color_name and color_price:
                    color = ProductColor(
                        product_id=new_product.product_id,
                        model_id=default_model.model_id,
                        name=color_name,
                        stock_quantity=int(color_stock),
                        price=float(color_price),
                        original_price=float(color_original_price) if color_original_price else None,
                        threshold=int(threshold)
                    )
                    db.session.add(color)
                    db.session.commit()

                    # Process color images
                    color_images = request.files.getlist(f'color_images_{i}')
                    for image_file in color_images:
                        image_url = save_image(image_file)
                        if image_url:
                            image = ProductImage(
                                product_id=new_product.product_id,
                                color_id=color.color_id,
                                image_url=image_url
                            )
                            db.session.add(image)

        # Handle Variable Product
        elif product_type == 'variable':
            models_count = int(request.form.get('models_count', 0))
            for i in range(models_count):
                model_name = request.form.get(f'model_name_{i}')
                model_description = request.form.get(f'model_description_{i}')

                if model_name and model_description:
                    model = ProductModel(
                        product_id=new_product.product_id,
                        name=model_name,
                        description=model_description
                    )
                    db.session.add(model)
                    db.session.commit()

                    # Process model specifications
                    model_specs_count = int(request.form.get(f'model_specs_count_{i}', 0))
                    for j in range(model_specs_count):
                        spec_key = request.form.get(f'model_{i}_spec_key_{j}')
                        spec_value = request.form.get(f'model_{i}_spec_value_{j}')
                        if spec_key and spec_value:
                            spec = ModelSpecification(
                                model_id=model.model_id,
                                key=spec_key,
                                value=spec_value
                            )
                            db.session.add(spec)

                    # Process model colors
                    model_colors_count = int(request.form.get(f'model_colors_count_{i}', 0))
                    for j in range(model_colors_count):
                        color_name = request.form.get(f'model_{i}_color_name_{j}')
                        color_price = request.form.get(f'model_{i}_color_price_{j}')
                        color_original_price = request.form.get(f'model_{i}_color_original_price_{j}')
                        color_stock = request.form.get(f'model_{i}_color_stock_{j}', 0)
                        threshold = request.form.get(f'model_{i}_threshold_{j}', 10)

                        if color_name and color_price:
                            color = ProductColor(
                                product_id=new_product.product_id,
                                model_id=model.model_id,
                                name=color_name,
                                stock_quantity=int(color_stock),
                                price=float(color_price),
                                original_price=float(color_original_price) if color_original_price else None,
                                threshold=int(threshold)
                            )
                            db.session.add(color)
                            db.session.commit()

                            # Process color images
                            color_images = request.files.getlist(f'model_{i}_color_images_{j}')
                            for image_file in color_images:
                                image_url = save_image(image_file)
                                if image_url:
                                    image = ProductImage(
                                        product_id=new_product.product_id,
                                        color_id=color.color_id,
                                        image_url=image_url
                                    )
                                    db.session.add(image)
        
        hsn_code = ""
        if hsn_id:
            hsn_code = db.session.query(HSN.hsn_code).filter(HSN.hsn_id == hsn_id).scalar() or "NA"
        else:
            hsn_code = "NA"

        # Format the SKU ID
        sku_id = f"{category_id}-{subcategory_id}-{hsn_code}-{new_product.product_id}"

        # Update the product with the SKU ID
        new_product.sku_id = sku_id


        # Commit all changes
        db.session.commit()


        logger.info(f"Product added by admin: {request.current_user.email} - Product ID: {new_product.product_id}")

        return jsonify({
            'message': 'Product added successfully!',
            'product_id': new_product.product_id
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding product by {request.current_user.email}: {str(e)}")
        return jsonify({'message': f'An error occurred while adding the product: {str(e)}'}), 500


# ADD HSN 
@products_bp.route('/hsn/add', methods=['POST'])
@token_required(roles=['admin'])
def add_hsn():
    try:
        data = request.get_json()  # Accept JSON data
        hsn_code = data.get('hsn_code')
        description = data.get('description')
        gst_rate = data.get('gst_rate', None)  # Default to None if gst_rate is not provided

        # Log the received HSN code and description
        print(f"Received HSN Code: {hsn_code}, Description: {description}")

        if not hsn_code or not description:
            return jsonify({'message': 'HSN code and description are required'}), 400

        # Check if the HSN code already exists
        existing_hsn = HSN.query.filter_by(hsn_code=hsn_code).first()
        if existing_hsn:
            return jsonify({'message': 'HSN code already exists'}), 400

        new_hsn = HSN(hsn_code=hsn_code, hsn_description=description, gst_rate=gst_rate)
        db.session.add(new_hsn)
        db.session.commit()

        # Log the success of HSN addition
        print(f"HSN Code '{hsn_code}' added successfully!")

        return jsonify({
            'message': 'HSN added successfully!',
            'hsn_id': new_hsn.hsn_id,
            'hsn_code': new_hsn.hsn_code,
            'description': new_hsn.hsn_description,
            'gst_rate': new_hsn.gst_rate  # Returning gst_rate to confirm
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding HSN: {str(e)}")
        return jsonify({'message': 'An error occurred while adding the HSN'}), 500


@products_bp.route('/category/add', methods=['POST'])
@token_required(roles=['admin'])
def add_category():
    try:
        name = request.form.get('name')
        image = request.files.get('image')

        if not name:
            return jsonify({'message': 'Category name is required'}), 400

        # Case-insensitive check
        existing_category = Category.query.filter(func.lower(Category.name) == name.lower()).first()
        if existing_category:
            return jsonify({'message': 'Category name already exists'}), 400

        image_url = save_image(image)

        new_category = Category(name=name, image_url=image_url)
        db.session.add(new_category)
        db.session.commit()

        return jsonify({
            'message': 'Category added successfully!',
            'category_id': new_category.category_id,
            'name': new_category.name,
            'image_url': image_url
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding category: {str(e)}")
        return jsonify({'message': 'An error occurred while adding the category'}), 500



# Add subcategory endpoint
@products_bp.route('/subcategory/add', methods=['POST'])
@token_required(roles=['admin'])
def add_subcategory():
    try:
        name = request.json.get('name')
        category_id = request.json.get('category_id')
        
        if not name or not category_id:
            return jsonify({'message': 'Subcategory name and category_id are required'}), 400
        
        category = Category.query.get(category_id)
        if not category:
            return jsonify({'message': 'Category not found'}), 404

        # Case-insensitive duplicate check for subcategory within the same category
        existing_subcategory = Subcategory.query.filter(
            func.lower(Subcategory.name) == name.lower(),
            Subcategory.category_id == category_id
        ).first()
        if existing_subcategory:
            return jsonify({'message': 'Subcategory name already exists in this category'}), 400

        new_subcategory = Subcategory(name=name, category_id=category_id)
        db.session.add(new_subcategory)
        db.session.commit()

        return jsonify({
            'message': 'Subcategory added successfully!',
            'subcategory_id': new_subcategory.subcategory_id,
            'name': new_subcategory.name,
            'category_id': new_subcategory.category_id
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding subcategory: {str(e)}")
        return jsonify({'message': 'An error occurred while adding the subcategory'}), 500



@products_bp.route('/products/by-category/<int:category_id>', methods=['GET'])
def get_products_by_category(category_id):
    products = Product.query.filter_by(category_id=category_id).all()

    result = []
    for product in products:
        result.append({
            'product_id': product.product_id,
            'name': product.name,
            'description': product.description,
            'category_id': product.category_id,
            'subcategory_id': product.subcategory_id,
            'hsn': product.hsn.hsn_code if product.hsn else None,
            'sku_id': product.sku_id,
            'product_type': product.product_type,
            'rating': product.rating,
            'raters': product.raters,
            'created_at': product.created_at.isoformat(),
            'updated_at': product.updated_at.isoformat(),
            # 'unit': product.unit,
            'images': [img.image_url for img in product.images],
            'colors': [{
                'color_id': color.color_id,
                'name': color.name,
                'price': float(color.price),
                'original_price': float(color.original_price),
                'stock_quantity': color.stock_quantity
            } for color in product.colors],
            'specifications': [{
                'key': spec.key,
                'value': spec.value
            } for spec in product.specifications]
        })

    return jsonify(result), 200



    # EDIT PRODUCTS 


# Update an entire product (PUT)
@products_bp.route('/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    product = Product.query.get_or_404(product_id)
    data = request.form.to_dict() if request.form else request.json
    
    # Update basic product information
    product.name = data.get('name', product.name)
    product.description = data.get('description', product.description)
    product.category_id = data.get('category_id', product.category_id)
    product.subcategory_id = data.get('subcategory_id', product.subcategory_id)
    product.product_type = data.get('product_type', product.product_type)
    product.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        return jsonify({'message': 'Product updated successfully', 'product_id': product.product_id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# Partially update a product (PATCH)
@products_bp.route('/<int:product_id>', methods=['PATCH'])
def partially_update_product(product_id):
    product = Product.query.get_or_404(product_id)
    data = request.form.to_dict() if request.form else request.json
    
    # Update only the fields that are provided
    if 'name' in data:
        product.name = data['name']
    if 'description' in data:
        product.description = data['description']
    if 'category_id' in data:
        product.category_id = data['category_id']
    if 'subcategory_id' in data:
        product.subcategory_id = data['subcategory_id']
    if 'product_type' in data:
        product.product_type = data['product_type']
  
    
    product.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        return jsonify({'message': 'Product partially updated', 'product_id': product.product_id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# Delete a product
@products_bp.route('/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    # First delete all related cart items
    try:
        # Delete cart items associated with this product
        CartItem.query.filter_by(product_id=product_id).delete()
        WishlistItem.query.filter_by(product_id=product_id).delete()

        
        # Get all image paths to delete files from filesystem
        image_paths = []
        for image in product.images:
            if image.image_url and not image.image_url.startswith('http'):
                image_paths.append(image.image_url.replace('/product_images/', ''))
        
        # Delete product from database (cascade will handle other related records)
        db.session.delete(product)
        db.session.commit()
        
        # Delete image files from filesystem
        for img_path in image_paths:
            try:
                file_path = os.path.join(UPLOAD_FOLDER, img_path)
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                # Log error but continue with other operations
                print(f"Error deleting file {img_path}: {str(e)}")
        
        return jsonify({'message': 'Product deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    


# ----- Product Images Routes -----
# UPDATE COVER IMAGE 

# Update cover image (special case of updating the first image)
@products_bp.route('/<int:product_id>/cover-image', methods=['POST'])
def update_cover_image(product_id):
    # Get the first image for this product (lowest image_id)
    first_image = ProductImage.query.filter_by(product_id=product_id)\
                                  .order_by(ProductImage.image_id.asc())\
                                  .first()
    
    if not first_image:
        return jsonify({'error': 'No images found for this product'}), 404
    
    # Check if image file is provided
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    image_file = request.files['image']
    new_image_url = save_image(image_file)
    
    if not new_image_url:
        return jsonify({'error': 'Invalid image file'}), 400
    
    # Store old path for cleanup
    old_image_path = None
    if first_image.image_url and not first_image.image_url.startswith('http'):
        old_image_path = first_image.image_url.replace('/product_images/', '')
    
    # Update the image URL
    first_image.image_url = new_image_url
    
    try:
        db.session.commit()
        
        # Delete old image file if replaced
        if old_image_path and new_image_url != f'/product_images/{old_image_path}':
            try:
                file_path = os.path.join(UPLOAD_FOLDER, old_image_path)
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Error deleting file {old_image_path}: {str(e)}")
        
        return jsonify({
            'message': 'Cover image updated successfully',
            'image_id': first_image.image_id,
            'image_url': new_image_url
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    

# Add new product image
@products_bp.route('/<int:product_id>/images', methods=['POST'])
def add_product_image(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Check if image file is provided
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    image_file = request.files['image']
    image_url = save_image(image_file)
    
    if not image_url:
        return jsonify({'error': 'Invalid image file'}), 400
    
    # Get color_id from form data if available
    color_id = None
    if request.form and 'color_id' in request.form:
        color_id = request.form.get('color_id')
    
    new_image = ProductImage(
        product_id=product_id,
        color_id=color_id,
        image_url=image_url
    )
    
    try:
        db.session.add(new_image)
        db.session.commit()
        return jsonify({
            'message': 'Image added successfully',
            'image_id': new_image.image_id,
            'image_url': image_url
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


# Update product image
@products_bp.route('/<int:product_id>/images/<int:image_id>', methods=['PUT'])
def update_product_image(product_id, image_id):
    image = ProductImage.query.get_or_404(image_id)
    if image.product_id != product_id:
        return jsonify({'error': 'Image does not belong to this product'}), 400
    
    old_image_path = None
    if image.image_url and not image.image_url.startswith('http'):
        old_image_path = image.image_url.replace('/product_images/', '')
    
    # Check if a new image file is provided
    if 'image' in request.files:
        image_file = request.files['image']
        image_url = save_image(image_file)
        
        if image_url:
            image.image_url = image_url
    
    # Update color_id if provided
    if request.form and 'color_id' in request.form:
        image.color_id = request.form.get('color_id')
    
    try:
        db.session.commit()
        
        # Delete old image file if replaced
        if old_image_path and image.image_url != f'/product_images/{old_image_path}':
            try:
                file_path = os.path.join(UPLOAD_FOLDER, old_image_path)
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                # Log error but continue with other operations
                print(f"Error deleting file {old_image_path}: {str(e)}")
        
        return jsonify({
            'message': 'Image updated successfully',
            'image_url': image.image_url
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# Delete product image
@products_bp.route('/<int:product_id>/images/<int:image_id>', methods=['DELETE'])
def delete_product_image(product_id, image_id):
    image = ProductImage.query.get_or_404(image_id)
    if image.product_id != product_id:
        return jsonify({'error': 'Image does not belong to this product'}), 400
    
    # Store image path to delete file after database record
    image_path = None
    if image.image_url and not image.image_url.startswith('http'):
        image_path = image.image_url.replace('/product_images/', '')
    
    try:
        db.session.delete(image)
        db.session.commit()
        
        # Delete image file from filesystem
        if image_path:
            try:
                file_path = os.path.join(UPLOAD_FOLDER, image_path)
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                # Log error but continue with other operations
                print(f"Error deleting file {image_path}: {str(e)}")
        
        return jsonify({'message': 'Image deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# ----- Product Models Routes -----

# Add new product model
@products_bp.route('/<int:product_id>/models', methods=['POST'])
def add_product_model(product_id):
    product = Product.query.get_or_404(product_id)
    data = request.form.to_dict() if request.form else request.json
    
    new_model = ProductModel(
        product_id=product_id,
        name=data['name'],
        description=data['description']
    )
    
    try:
        db.session.add(new_model)
        db.session.commit()
        return jsonify({'message': 'Model added successfully', 'model_id': new_model.model_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# Update product model
@products_bp.route('/<int:product_id>/models/<int:model_id>', methods=['PUT'])
def update_product_model(product_id, model_id):
    model = ProductModel.query.get_or_404(model_id)
    if model.product_id != product_id:
        return jsonify({'error': 'Model does not belong to this product'}), 400
        
    data = request.form.to_dict() if request.form else request.json
    
    model.name = data.get('name', model.name)
    model.description = data.get('description', model.description)
    
    try:
        db.session.commit()
        return jsonify({'message': 'Model updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# Delete product model
@products_bp.route('/<int:product_id>/models/<int:model_id>', methods=['DELETE'])
def delete_product_model(product_id, model_id):
    model = ProductModel.query.get_or_404(model_id)
    if model.product_id != product_id:
        return jsonify({'error': 'Model does not belong to this product'}), 400
    
    try:
        db.session.delete(model)
        db.session.commit()
        return jsonify({'message': 'Model deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# ----- Product Colors Routes -----

# Add new product color
@products_bp.route('/<int:product_id>/colors', methods=['POST'])
def add_product_color(product_id):
    product = Product.query.get_or_404(product_id)
    data = request.form.to_dict() if request.form else request.json
    
    new_color = ProductColor(
        product_id=product_id,
        model_id=data.get('model_id'),
        name=data['name'],
        stock_quantity=data.get('stock_quantity', 0),
        price=data['price'],
        original_price=data.get('original_price'),
        threshold=data.get('threshold', 10)
    )
    
    try:
        db.session.add(new_color)
        db.session.commit()
        return jsonify({'message': 'Color added successfully', 'color_id': new_color.color_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# Update product color
@products_bp.route('/<int:product_id>/colors/<int:color_id>', methods=['PUT'])
def update_product_color(product_id, color_id):
    color = ProductColor.query.get_or_404(color_id)
    if color.product_id != product_id:
        return jsonify({'error': 'Color does not belong to this product'}), 400
        
    data = request.form.to_dict() if request.form else request.json
    
    color.model_id = data.get('model_id', color.model_id)
    color.name = data.get('name', color.name)
    color.stock_quantity = data.get('stock_quantity', color.stock_quantity)
    color.price = data.get('price', color.price)
    color.original_price = data.get('original_price', color.original_price)
    color.threshold = data.get('threshold', color.threshold)
    
    try:
        db.session.commit()
        return jsonify({'message': 'Color updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


# Partially update product color (specifically for stock update)
@products_bp.route('/<int:product_id>/colors/<int:color_id>', methods=['PUT'])
def partially_update_product_color(product_id, color_id):
    color = ProductColor.query.get_or_404(color_id)
    if color.product_id != product_id:
        return jsonify({'error': 'Color does not belong to this product'}), 400
        
    data = request.form.to_dict() if request.form else request.json
    
    if 'stock_quantity' in data:
        color.stock_quantity = data['stock_quantity']
    if 'price' in data:
        color.price = data['price']
    if 'original_price' in data:
        color.original_price = data['original_price']
    if 'threshold' in data:
        color.threshold = data['threshold']
    if 'name' in data:
        color.name = data['name']
    if 'model_id' in data:
        color.model_id = data['model_id']
    
    try:
        db.session.commit()
        return jsonify({'message': 'Color partially updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# Delete product color
@products_bp.route('/<int:product_id>/colors/<int:color_id>', methods=['DELETE'])
def delete_product_color(product_id, color_id):
    color = ProductColor.query.get_or_404(color_id)
    if color.product_id != product_id:
        return jsonify({'error': 'Color does not belong to this product'}), 400
    
    try:
        db.session.delete(color)
        db.session.commit()
        return jsonify({'message': 'Color deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# ----- Product Specifications Routes -----

# Add new product specification
@products_bp.route('/<int:product_id>/specifications', methods=['POST'])
def add_product_specification(product_id):
    product = Product.query.get_or_404(product_id)
    data = request.form.to_dict() if request.form else request.json
    
    new_spec = ProductSpecification(
        product_id=product_id,
        key=data['key'],
        value=data['value']
    )
    
    try:
        db.session.add(new_spec)
        db.session.commit()
        return jsonify({'message': 'Specification added successfully', 'spec_id': new_spec.spec_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# Update product specification
@products_bp.route('/<int:product_id>/specifications/<int:spec_id>', methods=['PUT'])
def update_product_specification(product_id, spec_id):
    spec = ProductSpecification.query.get_or_404(spec_id)
    if spec.product_id != product_id:
        return jsonify({'error': 'Specification does not belong to this product'}), 400
        
    data = request.form.to_dict() if request.form else request.json
    
    spec.key = data.get('key', spec.key)
    spec.value = data.get('value', spec.value)
    
    try:
        db.session.commit()
        return jsonify({'message': 'Specification updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# Delete product specification
@products_bp.route('/<int:product_id>/specifications/<int:spec_id>', methods=['DELETE'])
def delete_product_specification(product_id, spec_id):
    spec = ProductSpecification.query.get_or_404(spec_id)
    if spec.product_id != product_id:
        return jsonify({'error': 'Specification does not belong to this product'}), 400
    
    try:
        db.session.delete(spec)
        db.session.commit()
        return jsonify({'message': 'Specification deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# ----- Model Specifications Routes -----

# Add new model specification
@products_bp.route('/<int:product_id>/models/<int:model_id>/specifications', methods=['POST'])
def add_model_specification(product_id, model_id):
    model = ProductModel.query.get_or_404(model_id)
    if model.product_id != product_id:
        return jsonify({'error': 'Model does not belong to this product'}), 400
        
    data = request.form.to_dict() if request.form else request.json
    
    new_spec = ModelSpecification(
        model_id=model_id,
        key=data['key'],
        value=data['value']
    )
    
    try:
        db.session.add(new_spec)
        db.session.commit()
        return jsonify({'message': 'Model specification added successfully', 'spec_id': new_spec.spec_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# Update model specification
@products_bp.route('/<int:product_id>/models/<int:model_id>/specifications/<int:spec_id>', methods=['PUT'])
def update_model_specification(product_id, model_id, spec_id):
    model = ProductModel.query.get_or_404(model_id)
    if model.product_id != product_id:
        return jsonify({'error': 'Model does not belong to this product'}), 400
        
    spec = ModelSpecification.query.get_or_404(spec_id)
    if spec.model_id != model_id:
        return jsonify({'error': 'Specification does not belong to this model'}), 400
        
    data = request.form.to_dict() if request.form else request.json
    
    spec.key = data.get('key', spec.key)
    spec.value = data.get('value', spec.value)
    
    try:
        db.session.commit()
        return jsonify({'message': 'Model specification updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# Delete model specification
@products_bp.route('/<int:product_id>/models/<int:model_id>/specifications/<int:spec_id>', methods=['DELETE'])
def delete_model_specification(product_id, model_id, spec_id):
    print(f"DELETE request for spec {spec_id} from model {model_id} in product {product_id}")
    
    # Verify model belongs to product
    model = ProductModel.query.get_or_404(model_id)
    if model.product_id != product_id:
        print("Error: Model doesn't belong to product")
        return jsonify({'error': 'Model does not belong to this product'}), 400
        
    # Verify spec belongs to model
    spec = ModelSpecification.query.get_or_404(spec_id)
    if spec.model_id != model_id:
        print("Error: Spec doesn't belong to model")
        return jsonify({'error': 'Specification does not belong to this model'}), 400
    
    try:
        print(f"Attempting to delete spec ID {spec_id}")
        db.session.delete(spec)
        db.session.commit()
        print("Deletion committed successfully")
        return jsonify({'message': 'Model specification deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error during deletion: {str(e)}")
        return jsonify({'error': str(e)}), 400
    

# Batch update product rating
@products_bp.route('/<int:product_id>/rating', methods=['PATCH'])
def update_product_rating(product_id):
    product = Product.query.get_or_404(product_id)
    data = request.form.to_dict() if request.form else request.json
    
    if 'rating' in data and 'raters' in data:
        product.rating = data['rating']
        product.raters = data['raters']
    elif 'rating' in data:
        # If adding a new rating
        new_rating = float(data['rating'])
        current_total = product.rating * product.raters
        product.raters += 1
        product.rating = (current_total + new_rating) / product.raters
    
    try:
        db.session.commit()
        return jsonify({'message': 'Product rating updated successfully', 'new_rating': product.rating}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400



# PRODUCTS STOKES 

@products_bp.route('/product/get/productstatus', methods=['GET'])
@token_required(roles=['admin'])
def get_product_status():
    results = []

    products = Product.query.all()

    for product in products:
        for model in product.models:
            for color in model.colors:
                # images = ProductImage.query.filter_by(
                #     product_id=product.product_id,
                #     color_id=color.color_id
                # ).all()
                images = ProductImage.query.filter_by(product_id=product.product_id).all()

                image_urls = [img.image_url for img in images]

                # This needs to be inside the color loop
                status='IN_STOCK'

                if(color.stock_quantity<=color.threshold):
                    status='LOW_STOCK'
                
                if(color.stock_quantity==0):
                      status='OUT_OF_STOCK'
                
                results.append({
                    "product_id": product.product_id,
                    "product_name": product.name,
                    "model_id": model.model_id,
                    "model_name": model.name,
                    "color_id": color.color_id,
                    "color_name": color.name,
                    "images": image_urls,
                    "stock_quantity": color.stock_quantity,
                    "threshold": color.threshold,
                    "status":status
                })
                
    return jsonify(results), 200


     
# CATEGORY AND SUBCATEGORY UPDATE 
# Update product category
@products_bp.route('/product/<int:product_id>/category', methods=['PUT'])
@token_required(roles=['admin'])
def update_product_category(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        data = request.json
        
        category_id = data.get('category_id')
        if not category_id:
            return jsonify({'error': 'Category ID is required'}), 400
            
        # Verify the category exists
        category = Category.query.get(category_id)
        if not category:
            return jsonify({'error': 'Category not found'}), 404
            
        # Update the category
        product.category_id = category_id
        # When changing category, reset subcategory if it doesn't belong to the new category
        if product.subcategory_id:
            subcategory = Subcategory.query.get(product.subcategory_id)
            if subcategory and subcategory.category_id != category_id:
                product.subcategory_id = None
        
        product.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Product category updated by admin: {request.current_user.email} - Product ID: {product_id}")
        
        return jsonify({
            'message': 'Product category updated successfully',
            'product_id': product.product_id,
            'category_id': product.category_id,
            'category_name': category.name
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating product category: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Update product subcategory
@products_bp.route('/product/<int:product_id>/subcategory', methods=['PUT'])
@token_required(roles=['admin'])
def update_product_subcategory(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        data = request.json
        
        subcategory_id = data.get('subcategory_id')
        if subcategory_id is None:  # Allow setting to null/None
            product.subcategory_id = None
        else:
            # Verify the subcategory exists and belongs to the product's category
            subcategory = Subcategory.query.get(subcategory_id)
            if not subcategory:
                return jsonify({'error': 'Subcategory not found'}), 404
                
            if subcategory.category_id != product.category_id:
                return jsonify({'error': 'Subcategory does not belong to the product\'s category'}), 400
                
            product.subcategory_id = subcategory_id
        
        product.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Product subcategory updated by admin: {request.current_user.email} - Product ID: {product_id}")
        
        return jsonify({
            'message': 'Product subcategory updated successfully',
            'product_id': product.product_id,
            'subcategory_id': product.subcategory_id,
            'subcategory_name': Subcategory.query.get(product.subcategory_id).name if product.subcategory_id else None
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating product subcategory: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Update both category and subcategory in one request
@products_bp.route('/product/<int:product_id>/categorization', methods=['PUT'])
@token_required(roles=['admin'])
def update_product_categorization(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        data = request.json
        
        category_id = data.get('category_id')
        subcategory_id = data.get('subcategory_id')
        
        if not category_id:
            return jsonify({'error': 'Category ID is required'}), 400
            
        # Verify the category exists
        category = Category.query.get(category_id)
        if not category:
            return jsonify({'error': 'Category not found'}), 404
            
        # Update the category
        product.category_id = category_id
        
        # Handle subcategory
        if subcategory_id:
            # Verify the subcategory exists and belongs to the selected category
            subcategory = Subcategory.query.get(subcategory_id)
            if not subcategory:
                return jsonify({'error': 'Subcategory not found'}), 404
                
            if subcategory.category_id != category_id:
                return jsonify({'error': 'Subcategory does not belong to the selected category'}), 400
                
            product.subcategory_id = subcategory_id
        else:
            # If no subcategory provided, set to None
            product.subcategory_id = None
        
        product.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Product categorization updated by admin: {request.current_user.email} - Product ID: {product_id}")
        
        response = {
            'message': 'Product categorization updated successfully',
            'product_id': product.product_id,
            'category_id': product.category_id,
            'category_name': category.name,
            'subcategory_id': product.subcategory_id
        }
        
        if product.subcategory_id:
            response['subcategory_name'] = Subcategory.query.get(product.subcategory_id).name
        
        return jsonify(response), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating product categorization: {str(e)}")
        return jsonify({'error': str(e)}), 500


# Update product HSN code
@products_bp.route('/update/<int:product_id>/hsn', methods=['PUT'])
@token_required(roles=['admin'])
def update_product_hsn(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        data = request.json
        
        hsn_id = data.get('hsn_id')
        if not hsn_id:
            return jsonify({'error': 'HSN ID is required'}), 400
            
        # Verify the HSN exists
        hsn = HSN.query.get(hsn_id)
        if not hsn:
            return jsonify({'error': 'HSN code not found'}), 404
            
        # Update the HSN
        product.hsn_id = hsn_id
        product.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Product HSN updated by admin: {request.current_user.email} - Product ID: {product_id}")
        
        return jsonify({
            'message': 'Product HSN updated successfully',
            'product_id': product.product_id,
            'hsn_id': product.hsn_id,
            'hsn_code': hsn.hsn_code,
            'hsn_description': hsn.hsn_description
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating product HSN: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Edit existing HSN entry
@products_bp.route('/edit/hsn/<int:hsn_id>', methods=['PUT'])
# @products_bp.route('/edit/hsn/<int:hsn_id>', methods=['POST'])
@token_required(roles=['admin'])
def edit_hsn(hsn_id):
    try:
        hsn = HSN.query.get_or_404(hsn_id)
        data = request.get_json()
        
        hsn_code = data.get('hsn_code')
        description = data.get('description')
        gst_rate = data.get('gst_rate')
        
        if not hsn_code or not description:
            return jsonify({'message': 'HSN code and description are required'}), 400

        # Check if the new HSN code already exists (excluding current record)
        existing_hsn = HSN.query.filter(
            HSN.hsn_code == hsn_code,
            HSN.hsn_id != hsn_id
        ).first()
        
        if existing_hsn:
            return jsonify({'message': 'HSN code already exists'}), 400

        # Update the HSN record
        hsn.hsn_code = hsn_code
        hsn.hsn_description = description
        hsn.gst_rate = gst_rate
        
        db.session.commit()
        
        logger.info(f"HSN code updated by admin: {request.current_user.email} - HSN ID: {hsn_id}")
        
        return jsonify({
            'message': 'HSN updated successfully!',
            'hsn_id': hsn.hsn_id,
            'hsn_code': hsn.hsn_code,
            'description': hsn.hsn_description,
            'gst_rate': hsn.gst_rate
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating HSN: {str(e)}")
        return jsonify({'message': 'An error occurred while updating the HSN'}), 500

# EDIT CATEGORY AND SUBCATEGORY

#  CATEGORY 
@products_bp.route('/category/<int:category_id>', methods=['PUT'])
@token_required(roles=['admin'])
def update_category(category_id):
    try:
        data = request.json
        category = Category.query.get_or_404(category_id)

        name = data.get('name')
        image_url = data.get('image_url')

        if name:
            category.name = name
        if image_url:
            category.image_url = image_url

        db.session.commit()
        logger.info(f"Category updated by admin: {request.current_user.email} - Category ID: {category_id}")

        return jsonify({
            'message': 'Category updated successfully',
            'category_id': category.category_id,
            'name': category.name,
            'image_url': category.image_url
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating category: {str(e)}")
        return jsonify({'error': str(e)}), 500


 # SUBCATEGORY 

@products_bp.route('/subcategory/<int:subcategory_id>', methods=['PUT'])
@token_required(roles=['admin'])
def update_subcategory(subcategory_id):
    try:
        data = request.json
        subcategory = Subcategory.query.get_or_404(subcategory_id)

        name = data.get('name')
        if name:
            subcategory.name = name

        db.session.commit()
        logger.info(f"Subcategory updated by admin: {request.current_user.email} - Subcategory ID: {subcategory_id}")

        return jsonify({
            'message': 'Subcategory updated successfully',
            'subcategory_id': subcategory.subcategory_id,
            'name': subcategory.name
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating subcategory: {str(e)}")
        return jsonify({'error': str(e)}), 500


# DELETE Category AND SUBCATEGORY 


# Delete a category

@products_bp.route('/delete/category/<int:category_id>', methods=['DELETE'])
@token_required(roles=['admin'])
def delete_category(category_id):
    try:
        category = Category.query.get_or_404(category_id)

        # Check if any product is using this category
        product_using_category = Product.query.filter_by(category_id=category_id).first()
        if product_using_category:
            return jsonify({'error': 'Cannot delete. Category is assigned to one or more products.'}), 400

        db.session.delete(category)
        db.session.commit()
        logger.info(f"Category deleted by admin: {request.current_user.email} - Category ID: {category_id}")
        return jsonify({'message': 'Category deleted successfully'}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting category: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


 # Delete a subcategory

@products_bp.route('/delete/subcategory/<int:subcategory_id>', methods=['DELETE'])
@token_required(roles=['admin'])
def delete_subcategory(subcategory_id):
    try:
        subcategory = Subcategory.query.get_or_404(subcategory_id)

        # Check if any product is using this subcategory
        product_using_subcategory = Product.query.filter_by(subcategory_id=subcategory_id).first()
        if product_using_subcategory:
            return jsonify({'error': 'Cannot delete. Subcategory is assigned to one or more products.'}), 400

        db.session.delete(subcategory)
        db.session.commit()
        logger.info(f"Subcategory deleted by admin: {request.current_user.email} - Subcategory ID: {subcategory_id}")
        return jsonify({'message': 'Subcategory deleted successfully'}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting subcategory: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
    



# Delete HSN code
@products_bp.route('/delete/hsn/<int:hsn_id>', methods=['DELETE'])
@token_required(roles=['admin'])
def delete_hsn(hsn_id):
    try:
        hsn = HSN.query.get_or_404(hsn_id)

        # Check if any product is using this HSN
        product_using_hsn = Product.query.filter_by(hsn_id=hsn_id).first()
        if product_using_hsn:
            return jsonify({'error': 'Cannot delete. HSN code is assigned to one or more products.'}), 400

        db.session.delete(hsn)
        db.session.commit()
        
        logger.info(f"HSN code deleted by admin: {request.current_user.email} - HSN ID: {hsn_id}")
        return jsonify({'message': 'HSN code deleted successfully'}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting HSN code: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500




@products_bp.route('/products/<string:product_slug>', methods=['GET'])
def product_slug_meta(product_slug):
    try:
        # Use the same logic as your get_product_by_slug endpoint to find the product
        # First, try to handle special characters and formatting
        name = unquote(product_slug).replace('-', ' ')
        
        product = Product.query.options(
            db.joinedload(Product.images),
            db.joinedload(Product.main_category),
            db.joinedload(Product.sub_category),
            db.joinedload(Product.hsn),
            db.joinedload(Product.models).joinedload(ProductModel.colors).joinedload(ProductColor.images),
            db.joinedload(Product.models).joinedload(ProductModel.specifications),
            db.joinedload(Product.colors).joinedload(ProductColor.images)
        ).filter(
            func.replace(Product.name, '-', ' ').ilike(f'%{name}%')
        ).first()
        
        if not product:
            return "Product not found", 404
        
        # Get primary image URL with the correct /api/ prefix
        primary_image_url = ''
        if product.images and len(product.images) > 0:
            image_path = product.images[0].image_url
            
            # Make sure we include /api/ in the path
            if image_path.startswith('product_images/'):
                # Add /api/ prefix to image path if it's not already there
                primary_image_url = f"https://mtm-store.com/api/{image_path}"
            else:
                # Handle other path formats
                primary_image_url = f"https://mtm-store.com/api/{image_path.lstrip('/')}"
        
        logger.info(f"Slug: {product_slug}")
        logger.info(f"Product ID: {product.product_id}")
        logger.info(f"Converted image URL: {primary_image_url}")
        
        # Direct HTML rendering for meta tags
        meta_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta property="og:title" content="{product.name}">
    <meta property="og:description" content="{product.description}">
    <meta property="og:image" content="{primary_image_url}">
    <meta property="og:type" content="product">
    <meta property="og:url" content="https://mtm-store.com/products/{product_slug}">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{product.name}">
    <meta name="twitter:description" content="{product.description}">
    <meta name="twitter:image" content="{primary_image_url}">
    <meta name="description" content="{product.description}">
    <title>{product.name}</title>
</head>
<body>
    <h1>{product.name}</h1>
    <p>{product.description}</p>
    <img src="{primary_image_url}" alt="{product.name}" />
</body>
</html>"""
        return meta_html, 200, {'Content-Type': 'text/html; charset=utf-8'}
    
    except Exception as e:
        logger.error(f"Error generating product meta for slug {product_slug}: {str(e)}")
        return "Product not found", 404