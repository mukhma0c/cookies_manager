from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from models import db, Ingredient, Packaging, Purchase, OrderIngredient, OrderPackaging
from datetime import datetime
from sqlalchemy import func
import os
from werkzeug.utils import secure_filename
import uuid

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')

# Helper functions for file uploads
def allowed_file(filename):
    """Check if file has an allowed extension."""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file, item_type):
    """Save uploaded file with a unique name."""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Create a unique filename to prevent overwrites
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        # Create directory if it doesn't exist
        save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], item_type)
        os.makedirs(save_path, exist_ok=True)
        file_path = os.path.join(save_path, unique_filename)
        file.save(file_path)
        # Return the relative path to store in the database
        return os.path.join('img', item_type, unique_filename)
    return None

# Routes for Ingredients
@inventory_bp.route('/ingredients')
def list_ingredients():
    """Display all ingredients."""
    ingredients = Ingredient.query.order_by(Ingredient.name).all()
    return render_template('inventory/ingredients.html', ingredients=ingredients)

@inventory_bp.route('/ingredients/new', methods=['GET', 'POST'])
def add_ingredient():
    """Add a new ingredient."""
    if request.method == 'POST':
        name = request.form.get('name')
        default_unit = request.form.get('default_unit')
        default_price_per_unit_cents = request.form.get('default_price_per_unit_cents', type=int)
        low_stock_threshold = request.form.get('low_stock_threshold', type=float)
        notes = request.form.get('notes')
        
        # Check if ingredient with same name already exists
        existing = Ingredient.query.filter_by(name=name).first()
        if existing:
            flash(f'Ingredient "{name}" already exists.', 'danger')
            return redirect(url_for('inventory.add_ingredient'))
        
        # Create new ingredient
        ingredient = Ingredient(
            name=name,
            default_unit=default_unit,
            default_price_per_unit_cents=default_price_per_unit_cents,
            low_stock_threshold=low_stock_threshold,
            notes=notes
        )
        
        # Handle image upload
        file = request.files.get('image')
        if file and file.filename:
            image_path = save_file(file, 'ingredients')
            if image_path:
                ingredient.image_path = image_path
        
        db.session.add(ingredient)
        db.session.commit()
        flash(f'Ingredient "{name}" added successfully.', 'success')
        return redirect(url_for('inventory.list_ingredients'))
        
    return render_template('inventory/ingredient_form.html', ingredient=None)

@inventory_bp.route('/ingredients/<int:ingredient_id>/edit', methods=['GET', 'POST'])
def edit_ingredient(ingredient_id):
    """Edit an existing ingredient."""
    ingredient = Ingredient.query.get_or_404(ingredient_id)
    
    if request.method == 'POST':
        ingredient.name = request.form.get('name')
        ingredient.default_unit = request.form.get('default_unit')
        ingredient.default_price_per_unit_cents = request.form.get('default_price_per_unit_cents', type=int)
        ingredient.low_stock_threshold = request.form.get('low_stock_threshold', type=float)
        ingredient.notes = request.form.get('notes')
        
        # Handle image upload
        file = request.files.get('image')
        if file and file.filename:
            image_path = save_file(file, 'ingredients')
            if image_path:
                # Delete old image if it exists
                if ingredient.image_path:
                    try:
                        old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], ingredient.image_path)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    except Exception as e:
                        current_app.logger.error(f"Error deleting file: {e}")
                
                ingredient.image_path = image_path
        
        db.session.commit()
        flash(f'Ingredient "{ingredient.name}" updated successfully.', 'success')
        return redirect(url_for('inventory.list_ingredients'))
        
    return render_template('inventory/ingredient_form.html', ingredient=ingredient)

@inventory_bp.route('/ingredients/<int:ingredient_id>/delete', methods=['POST'])
def delete_ingredient(ingredient_id):
    """Delete an ingredient."""
    ingredient = Ingredient.query.get_or_404(ingredient_id)
    
    try:
        # Delete image file if it exists
        if ingredient.image_path:
            try:
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], ingredient.image_path)
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                current_app.logger.error(f"Error deleting file: {e}")
        
        name = ingredient.name
        db.session.delete(ingredient)
        db.session.commit()
        flash(f'Ingredient "{name}" deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting ingredient: {str(e)}', 'danger')
    
    return redirect(url_for('inventory.list_ingredients'))

# Routes for Packaging
@inventory_bp.route('/packaging')
def list_packaging():
    """Display all packaging items."""
    packaging_items = Packaging.query.order_by(Packaging.name).all()
    return render_template('inventory/packaging.html', packaging_items=packaging_items)

@inventory_bp.route('/packaging/new', methods=['GET', 'POST'])
def add_packaging():
    """Add a new packaging item."""
    if request.method == 'POST':
        name = request.form.get('name')
        default_unit = request.form.get('default_unit')
        default_price_per_unit_cents = request.form.get('default_price_per_unit_cents', type=int)
        low_stock_threshold = request.form.get('low_stock_threshold', type=float)
        notes = request.form.get('notes')
        
        # Check if packaging with same name already exists
        existing = Packaging.query.filter_by(name=name).first()
        if existing:
            flash(f'Packaging "{name}" already exists.', 'danger')
            return redirect(url_for('inventory.add_packaging'))
        
        # Create new packaging
        packaging = Packaging(
            name=name,
            default_unit=default_unit,
            default_price_per_unit_cents=default_price_per_unit_cents,
            low_stock_threshold=low_stock_threshold,
            notes=notes
        )
        
        # Handle image upload
        file = request.files.get('image')
        if file and file.filename:
            image_path = save_file(file, 'packaging')
            if image_path:
                packaging.image_path = image_path
        
        db.session.add(packaging)
        db.session.commit()
        flash(f'Packaging "{name}" added successfully.', 'success')
        return redirect(url_for('inventory.list_packaging'))
        
    return render_template('inventory/packaging_form.html', packaging=None)

@inventory_bp.route('/packaging/<int:packaging_id>/edit', methods=['GET', 'POST'])
def edit_packaging(packaging_id):
    """Edit an existing packaging item."""
    packaging = Packaging.query.get_or_404(packaging_id)
    
    if request.method == 'POST':
        packaging.name = request.form.get('name')
        packaging.default_unit = request.form.get('default_unit')
        packaging.default_price_per_unit_cents = request.form.get('default_price_per_unit_cents', type=int)
        packaging.low_stock_threshold = request.form.get('low_stock_threshold', type=float)
        packaging.notes = request.form.get('notes')
        
        # Handle image upload
        file = request.files.get('image')
        if file and file.filename:
            image_path = save_file(file, 'packaging')
            if image_path:
                # Delete old image if it exists
                if packaging.image_path:
                    try:
                        old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], packaging.image_path)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    except Exception as e:
                        current_app.logger.error(f"Error deleting file: {e}")
                
                packaging.image_path = image_path
        
        db.session.commit()
        flash(f'Packaging "{packaging.name}" updated successfully.', 'success')
        return redirect(url_for('inventory.list_packaging'))
        
    return render_template('inventory/packaging_form.html', packaging=packaging)

@inventory_bp.route('/packaging/<int:packaging_id>/delete', methods=['POST'])
def delete_packaging(packaging_id):
    """Delete a packaging item."""
    packaging = Packaging.query.get_or_404(packaging_id)
    
    try:
        # Delete image file if it exists
        if packaging.image_path:
            try:
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], packaging.image_path)
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                current_app.logger.error(f"Error deleting file: {e}")
        
        name = packaging.name
        db.session.delete(packaging)
        db.session.commit()
        flash(f'Packaging "{name}" deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting packaging: {str(e)}', 'danger')
    
    return redirect(url_for('inventory.list_packaging'))

@inventory_bp.route('/adjust', methods=['GET'])
def adjust_inventory():
    """Adjust inventory levels for ingredients and packaging."""
    # Calculate current ingredient stock levels
    ingredients_stock = []
    
    # Get all ingredients
    ingredients = Ingredient.query.order_by(Ingredient.name).all()
    
    for ingredient in ingredients:
        # Calculate total purchased
        total_purchased = db.session.query(func.sum(Purchase.quantity)).filter(
            Purchase.item_type == 'ingredient',
            Purchase.item_id == ingredient.id
        ).scalar() or 0
        
        # Calculate total used in orders
        total_used = db.session.query(func.sum(OrderIngredient.amount_used)).filter(
            OrderIngredient.ingredient_id == ingredient.id
        ).scalar() or 0
        
        # Current stock level
        current_stock = total_purchased - total_used
        
        ingredients_stock.append({
            'ingredient': ingredient,
            'current_stock': current_stock
        })
    
    # Calculate current packaging stock levels
    packaging_stock = []
    
    # Get all packaging items
    packaging_items = Packaging.query.order_by(Packaging.name).all()
    
    for packaging in packaging_items:
        # Calculate total purchased
        total_purchased = db.session.query(func.sum(Purchase.quantity)).filter(
            Purchase.item_type == 'packaging',
            Purchase.item_id == packaging.id
        ).scalar() or 0
        
        # Calculate total used in orders
        total_used = db.session.query(func.sum(OrderPackaging.quantity_used)).filter(
            OrderPackaging.packaging_id == packaging.id
        ).scalar() or 0
        
        # Current stock level
        current_stock = total_purchased - total_used
        
        packaging_stock.append({
            'packaging': packaging,
            'current_stock': current_stock
        })
    
    return render_template(
        'inventory/adjust.html',
        ingredients=ingredients_stock,
        packaging=packaging_stock
    )

@inventory_bp.route('/adjust/process', methods=['POST'])
def process_adjustment():
    """Process inventory adjustments and create adjustment records."""
    adjustment_count = 0
    
    # Process ingredient adjustments
    for key, value in request.form.items():
        if key.startswith('ingredient_'):
            try:
                ingredient_id = int(key.replace('ingredient_', ''))
                actual_stock = float(value)
                
                # Get the ingredient
                ingredient = Ingredient.query.get_or_404(ingredient_id)
                
                # Calculate current stock
                total_purchased = db.session.query(func.sum(Purchase.quantity)).filter(
                    Purchase.item_type == 'ingredient',
                    Purchase.item_id == ingredient_id
                ).scalar() or 0
                
                total_used = db.session.query(func.sum(OrderIngredient.amount_used)).filter(
                    OrderIngredient.ingredient_id == ingredient_id
                ).scalar() or 0
                
                current_stock = total_purchased - total_used
                
                # Calculate adjustment needed
                adjustment = actual_stock - current_stock
                
                # If there's an adjustment needed, create a purchase record
                if abs(adjustment) > 0.001:  # Use small epsilon to avoid floating point issues
                    purchase = Purchase(
                        purchase_date=datetime.utcnow().date(),
                        item_type='ingredient',
                        item_id=ingredient_id,
                        quantity=adjustment,
                        unit=ingredient.default_unit,
                        total_cost_cents=0,  # No cost for adjustments
                        notes=f"INVENTORY ADJUSTMENT: {'Addition' if adjustment > 0 else 'Reduction'} (not used for cost calculations)"
                    )
                    
                    # Mark as inventory adjustment with zero cost
                    purchase.unit_cost_cents = 0
                    
                    db.session.add(purchase)
                    adjustment_count += 1
            except (ValueError, TypeError):
                continue
        
        # Process packaging adjustments
        elif key.startswith('packaging_'):
            try:
                packaging_id = int(key.replace('packaging_', ''))
                actual_stock = float(value)
                
                # Get the packaging
                packaging = Packaging.query.get_or_404(packaging_id)
                
                # Calculate current stock
                total_purchased = db.session.query(func.sum(Purchase.quantity)).filter(
                    Purchase.item_type == 'packaging',
                    Purchase.item_id == packaging_id
                ).scalar() or 0
                
                total_used = db.session.query(func.sum(OrderPackaging.quantity_used)).filter(
                    OrderPackaging.packaging_id == packaging_id
                ).scalar() or 0
                
                current_stock = total_purchased - total_used
                
                # Calculate adjustment needed
                adjustment = actual_stock - current_stock
                
                # If there's an adjustment needed, create a purchase record
                if abs(adjustment) > 0.001:  # Use small epsilon to avoid floating point issues
                    purchase = Purchase(
                        purchase_date=datetime.utcnow().date(),
                        item_type='packaging',
                        item_id=packaging_id,
                        quantity=adjustment,
                        unit=packaging.default_unit,
                        total_cost_cents=0,  # No cost for adjustments
                        notes=f"INVENTORY ADJUSTMENT: {'Addition' if adjustment > 0 else 'Reduction'} (not used for cost calculations)"
                    )
                    
                    # Mark as inventory adjustment with zero cost
                    purchase.unit_cost_cents = 0
                    
                    db.session.add(purchase)
                    adjustment_count += 1
            except (ValueError, TypeError):
                continue
    
    # Commit changes if any adjustments were made
    if adjustment_count > 0:
        db.session.commit()
        flash(f'Successfully recorded {adjustment_count} inventory adjustments.', 'success')
    else:
        flash('No inventory adjustments were needed.', 'info')
    
    return redirect(url_for('inventory.adjust_inventory'))
