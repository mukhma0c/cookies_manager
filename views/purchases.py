from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Purchase, Ingredient, Packaging
from datetime import datetime

purchases_bp = Blueprint('purchases', __name__, url_prefix='/purchases')

@purchases_bp.route('/')
def list_purchases():
    """Display list of all purchases."""
    purchases = Purchase.query.order_by(Purchase.purchase_date.desc()).all()
    
    # Prepare purchases for display
    purchase_data = []
    for purchase in purchases:
        item_name = "Unknown"
        if purchase.item_type == 'ingredient':
            ingredient = Ingredient.query.get(purchase.item_id)
            if ingredient:
                item_name = ingredient.name
        else:  # packaging
            packaging = Packaging.query.get(purchase.item_id)
            if packaging:
                item_name = packaging.name
                
        purchase_data.append({
            'purchase': purchase,
            'item_name': item_name
        })
    
    return render_template('purchases/list.html', purchases=purchase_data)

@purchases_bp.route('/new', methods=['GET', 'POST'])
def add_purchase():
    """Add a new purchase."""
    if request.method == 'POST':
        item_type = request.form.get('item_type')
        item_id = request.form.get('item_id', type=int)
        purchase_date_str = request.form.get('purchase_date')
        quantity = request.form.get('quantity', type=float)
        unit = request.form.get('unit')
        total_cost_dollars = request.form.get('total_cost_dollars', type=float, default=0)
        notes = request.form.get('notes', '')
        
        # Convert dollars to cents
        total_cost_cents = int(total_cost_dollars * 100) if total_cost_dollars else 0
        
        # Parse date or use today
        try:
            purchase_date = datetime.strptime(purchase_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            purchase_date = datetime.utcnow().date()
        
        # Create purchase
        purchase = Purchase(
            item_type=item_type,
            item_id=item_id,
            purchase_date=purchase_date,
            quantity=quantity,
            unit=unit,
            total_cost_cents=total_cost_cents,
            notes=notes
        )
        
        # Calculate unit cost
        purchase.calculate_unit_cost()
        
        db.session.add(purchase)
        db.session.commit()
        
        flash(f'Purchase added successfully.', 'success')
        return redirect(url_for('purchases.list_purchases'))
    
    # Get all ingredients and packaging for the form
    ingredients = Ingredient.query.order_by(Ingredient.name).all()
    packaging_items = Packaging.query.order_by(Packaging.name).all()
    
    return render_template(
        'purchases/form.html', 
        purchase=None, 
        ingredients=ingredients, 
        packaging_items=packaging_items
    )

@purchases_bp.route('/<int:purchase_id>/edit', methods=['GET', 'POST'])
def edit_purchase(purchase_id):
    """Edit an existing purchase."""
    purchase = Purchase.query.get_or_404(purchase_id)
    
    if request.method == 'POST':
        item_type = request.form.get('item_type')
        item_id = request.form.get('item_id', type=int)
        purchase_date_str = request.form.get('purchase_date')
        quantity = request.form.get('quantity', type=float)
        unit = request.form.get('unit')
        total_cost_dollars = request.form.get('total_cost_dollars', type=float, default=0)
        notes = request.form.get('notes', '')
        
        # Convert dollars to cents
        total_cost_cents = int(total_cost_dollars * 100) if total_cost_dollars else 0
        
        # Parse date or use today
        try:
            purchase_date = datetime.strptime(purchase_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            purchase_date = datetime.utcnow().date()
        
        # Update purchase
        purchase.item_type = item_type
        purchase.item_id = item_id
        purchase.purchase_date = purchase_date
        purchase.quantity = quantity
        purchase.unit = unit
        purchase.total_cost_cents = total_cost_cents
        purchase.notes = notes
        
        # Recalculate unit cost
        purchase.calculate_unit_cost()
        
        db.session.commit()
        
        flash(f'Purchase updated successfully.', 'success')
        return redirect(url_for('purchases.list_purchases'))
    
    # Get all ingredients and packaging for the form
    ingredients = Ingredient.query.order_by(Ingredient.name).all()
    packaging_items = Packaging.query.order_by(Packaging.name).all()
    
    # Calculate total cost in dollars for display
    total_cost_dollars = purchase.total_cost_cents / 100 if purchase.total_cost_cents else 0
    
    return render_template(
        'purchases/form.html', 
        purchase=purchase, 
        ingredients=ingredients, 
        packaging_items=packaging_items,
        total_cost_dollars=total_cost_dollars
    )

@purchases_bp.route('/<int:purchase_id>/delete', methods=['POST'])
def delete_purchase(purchase_id):
    """Delete a purchase."""
    purchase = Purchase.query.get_or_404(purchase_id)
    
    db.session.delete(purchase)
    db.session.commit()
    
    flash('Purchase deleted successfully.', 'success')
    return redirect(url_for('purchases.list_purchases'))

@purchases_bp.route('/latest-costs')
def latest_costs():
    """View latest costs for all items."""
    # Get latest costs for ingredients
    ingredient_costs = []
    ingredients = Ingredient.query.order_by(Ingredient.name).all()
    
    for ingredient in ingredients:
        # Filter out zero-cost purchases (like inventory adjustments)
        latest_purchase = Purchase.query.filter_by(
            item_type='ingredient',
            item_id=ingredient.id
        ).filter(Purchase.unit_cost_cents > 0).order_by(Purchase.purchase_date.desc()).first()
        
        ingredient_costs.append({
            'item': ingredient,
            'latest_purchase': latest_purchase,
            'unit_cost_cents': latest_purchase.unit_cost_cents if latest_purchase else ingredient.default_price_per_unit_cents,
            'last_purchase_date': latest_purchase.purchase_date if latest_purchase else None
        })
    
    # Get latest costs for packaging
    packaging_costs = []
    packaging_items = Packaging.query.order_by(Packaging.name).all()
    
    for packaging in packaging_items:
        # Filter out zero-cost purchases (like inventory adjustments)
        latest_purchase = Purchase.query.filter_by(
            item_type='packaging',
            item_id=packaging.id
        ).filter(Purchase.unit_cost_cents > 0).order_by(Purchase.purchase_date.desc()).first()
        
        packaging_costs.append({
            'item': packaging,
            'latest_purchase': latest_purchase,
            'unit_cost_cents': latest_purchase.unit_cost_cents if latest_purchase else packaging.default_price_per_unit_cents,
            'last_purchase_date': latest_purchase.purchase_date if latest_purchase else None
        })
    
    return render_template(
        'purchases/latest_costs.html',
        ingredient_costs=ingredient_costs,
        packaging_costs=packaging_costs
    )
