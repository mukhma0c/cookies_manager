from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash, abort, session
from models import db, Order, Customer, Recipe, Ingredient, Packaging, OrderIngredient, OrderPackaging
from cost_helpers import calculate_order_cost_preview, snapshot_order_costs
from datetime import datetime

orders_bp = Blueprint('orders', __name__, url_prefix='/orders')

@orders_bp.route('/')
def list_orders():
    """Display list of all orders."""
    orders = Order.query.order_by(Order.order_date.desc()).all()
    return render_template('orders/list.html', orders=orders)

@orders_bp.route('/new', methods=['GET'])
def new_order_step1():
    """Step 1 of the order wizard: Customer & Recipe selection."""
    customers = Customer.query.order_by(Customer.name).all()
    recipes = Recipe.query.order_by(Recipe.name).all()
    
    # Pre-select recipe if provided in query string
    preselected_recipe_id = request.args.get('recipe_id', type=int)
    
    return render_template('orders/wizard_step1.html', 
                          customers=customers, 
                          recipes=recipes,
                          preselected_recipe_id=preselected_recipe_id)

@orders_bp.route('/new/step2', methods=['POST'])
def new_order_step2():
    """Step 2 of the order wizard: Ingredients selection."""
    # Get form data from step 1
    customer_id = request.form.get('customer_id', type=int)
    customer_name = request.form.get('customer_name')
    customer_type = request.form.get('customer_type')
    
    # Handle customer creation if needed
    if not customer_id and customer_name and customer_type:
        # Check if we need to create a new customer
        customer = Customer(
            name=customer_name,
            customer_type=customer_type
        )
        db.session.add(customer)
        db.session.commit()
        customer_id = customer.id
    
    form_data = {
        'customer_id': customer_id,
        'customer_name': customer_name,
        'customer_type': customer_type,
        'recipe_id': request.form.get('recipe_id', type=int),
        'cookie_size': request.form.get('cookie_size'),
        'quantity_ordered': request.form.get('quantity_ordered', type=int, default=0)
    }
    
    # Store in session for later steps
    session['order_wizard'] = form_data
    
    # If a recipe was selected, pre-populate ingredients
    ingredients = []
    recipe = None
    if form_data['recipe_id']:
        recipe = Recipe.query.get_or_404(form_data['recipe_id'])
        for ri in recipe.ingredients:
            ingredients.append({
                'id': ri.ingredient_id,
                'name': ri.ingredient.name,
                'amount': ri.quantity,
                'unit': ri.ingredient.default_unit
            })
    else:
        # If no recipe, show all ingredients
        all_ingredients = Ingredient.query.order_by(Ingredient.name).all()
        ingredients = [{'id': i.id, 'name': i.name, 'amount': 0, 'unit': i.default_unit} for i in all_ingredients]
    
    return render_template('orders/wizard_step2.html', 
                          ingredients=ingredients, 
                          recipe=recipe, 
                          form_data=form_data)

@orders_bp.route('/new/step3', methods=['POST'])
def new_order_step3():
    """Step 3 of the order wizard: Bake outcome."""
    # Make Customer model available to the template
    from models import Customer
    # Get ingredient selections from step 2
    ingredients = []
    for key, value in request.form.items():
        if key.startswith('ingredient_amount_') and float(value) > 0:
            ingredient_id = int(key.replace('ingredient_amount_', ''))
            ingredient = Ingredient.query.get(ingredient_id)
            ingredients.append({
                'id': ingredient_id,
                'name': ingredient.name,
                'amount': float(value),
                'unit': ingredient.default_unit
            })
    
    # Calculate dough weight if recipe was used
    recipe_id = request.form.get('recipe_id', type=int)
    dough_weight_g = 0
    recipe = None
    
    if recipe_id:
        recipe = Recipe.query.get(recipe_id)
        # Sum the weight of all ingredients
        for ingredient in ingredients:
            dough_weight_g += ingredient['amount']
    
    # Get other form data
    form_data = {
        'customer_id': request.form.get('customer_id', type=int),
        'customer_name': request.form.get('customer_name'),
        'customer_type': request.form.get('customer_type'),
        'recipe_id': recipe_id,
        'cookie_size': request.form.get('cookie_size'),
        'quantity_ordered': request.form.get('quantity_ordered', type=int, default=0),
        'ingredients': ingredients,
        'dough_weight_g': dough_weight_g
    }
    
    # Update session
    session['order_wizard'] = form_data
    
    return render_template('orders/wizard_step3.html', form_data=form_data, Customer=Customer)

@orders_bp.route('/new/step4', methods=['POST'])
def new_order_step4():
    """Step 4 of the order wizard: Packaging selection."""
    # Get data from step 3
    form_data = {
        'customer_id': request.form.get('customer_id', type=int),
        'customer_name': request.form.get('customer_name'),
        'customer_type': request.form.get('customer_type'),
        'recipe_id': request.form.get('recipe_id', type=int),
        'cookie_size': request.form.get('cookie_size'),
        'quantity_ordered': request.form.get('quantity_ordered', type=int, default=0),
        'quantity_baked': request.form.get('quantity_baked', type=int, default=0),
        'quantity_kept_family': request.form.get('quantity_kept_family', type=int, default=0),
        'dough_weight_g': request.form.get('dough_weight_g', type=float, default=0),
        'sale_price_total_cents': request.form.get('sale_price_total_cents', type=int, default=0)
    }
    
    # Get ingredients from previous step
    ingredients_data = session.get('order_wizard', {}).get('ingredients', [])
    form_data['ingredients'] = ingredients_data
    
    # Get all packaging options
    packaging = Packaging.query.order_by(Packaging.name).all()
    
    return render_template('orders/wizard_step4.html', 
                          packaging=packaging, 
                          form_data=form_data)

@orders_bp.route('/new/step5', methods=['POST'])
def new_order_step5():
    """Step 5 of the order wizard: Review & Save."""
    # Get packaging selections from step 4
    packaging_items = []
    for key, value in request.form.items():
        if key.startswith('packaging_quantity_') and float(value) > 0:
            packaging_id = int(key.replace('packaging_quantity_', ''))
            packaging = Packaging.query.get(packaging_id)
            packaging_items.append({
                'id': packaging_id,
                'name': packaging.name,
                'quantity': float(value),
                'unit': packaging.default_unit
            })
    
    # Get all form data
    form_data = {
        'customer_id': request.form.get('customer_id', type=int),
        'recipe_id': request.form.get('recipe_id', type=int),
        'cookie_size': request.form.get('cookie_size'),
        'quantity_ordered': request.form.get('quantity_ordered', type=int, default=0),
        'quantity_baked': request.form.get('quantity_baked', type=int, default=0),
        'quantity_kept_family': request.form.get('quantity_kept_family', type=int, default=0),
        'dough_weight_g': request.form.get('dough_weight_g', type=float, default=0),
        'packaging': packaging_items,
        'sale_price_total_cents': request.form.get('sale_price_total_cents', type=int, default=0)
    }
    
    # Get ingredients from session
    ingredients_data = session.get('order_wizard', {}).get('ingredients', [])
    form_data['ingredients'] = ingredients_data
    
    # Get customer and recipe for display
    customer = Customer.query.get(form_data['customer_id']) if form_data['customer_id'] else None
    recipe = Recipe.query.get(form_data['recipe_id']) if form_data['recipe_id'] else None
    
    # Calculate costs for preview
    cost_preview = calculate_order_cost_preview(
        [{'id': i['id'], 'amount': i['amount']} for i in form_data['ingredients']],
        [{'id': p['id'], 'quantity': p['quantity']} for p in form_data['packaging']]
    )
    
    return render_template('orders/wizard_step5.html', 
                          form_data=form_data,
                          customer=customer,
                          recipe=recipe,
                          cost_preview=cost_preview)

@orders_bp.route('/create', methods=['POST'])
def create_order():
    """Save the order to the database."""
    try:
        # Extract data from form
        customer_id = request.form.get('customer_id', type=int)
        customer_name = request.form.get('customer_name')
        customer_type = request.form.get('customer_type')
        recipe_id = request.form.get('recipe_id', type=int)
        cookie_size = request.form.get('cookie_size')
        dough_weight_g = request.form.get('dough_weight_g', type=float)
        quantity_ordered = request.form.get('quantity_ordered', type=int)
        quantity_baked = request.form.get('quantity_baked', type=int)
        quantity_kept_family = request.form.get('quantity_kept_family', type=int, default=0)
        sale_price_total_cents = request.form.get('sale_price_total_cents', type=int)
        notes = request.form.get('notes', '')
        
        # Create or get customer if needed
        if not customer_id and customer_name and customer_type:
            # Check if we need to create a new customer
            customer = Customer(
                name=customer_name,
                customer_type=customer_type
            )
            db.session.add(customer)
            db.session.flush()  # Get ID without committing
            customer_id = customer.id
        
        # Create new order
        order = Order(
            customer_id=customer_id,
            recipe_id=recipe_id,
            cookie_size=cookie_size,
            dough_weight_g=dough_weight_g,
            quantity_ordered=quantity_ordered,
            quantity_baked=quantity_baked,
            quantity_kept_family=quantity_kept_family,
            sale_price_total_cents=sale_price_total_cents,
            notes=notes,
            order_date=datetime.utcnow()
        )
        
        db.session.add(order)
        db.session.flush()  # Get order ID without committing
        
        # Parse ingredient data from form
        ingredients = []
        ingredient_keys = [k for k in request.form.keys() if k.startswith('ingredient_id_')]
        
        for key in ingredient_keys:
            idx = key.replace('ingredient_id_', '')
            ingredient_id = request.form.get(key, type=int)
            amount = request.form.get(f'ingredient_amount_{idx}', type=float)
            
            if ingredient_id and amount > 0:
                ingredients.append({
                    'id': ingredient_id,
                    'amount': amount
                })
        
        # Parse packaging data from form
        packaging = []
        packaging_keys = [k for k in request.form.keys() if k.startswith('packaging_id_')]
        
        for key in packaging_keys:
            idx = key.replace('packaging_id_', '')
            packaging_id = request.form.get(key, type=int)
            quantity = request.form.get(f'packaging_quantity_{idx}', type=float)
            
            if packaging_id and quantity > 0:
                packaging.append({
                    'id': packaging_id,
                    'quantity': quantity
                })
        
        # Create cost snapshots
        snapshot_order_costs(order, ingredients, packaging)
        
        db.session.commit()
        flash('Order created successfully!', 'success')
        return redirect(url_for('orders.list_orders'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating order: {str(e)}', 'danger')
        return redirect(url_for('orders.new_order_step1'))

@orders_bp.route('/<int:order_id>')
def view_order(order_id):
    """View a single order's details."""
    order = Order.query.get_or_404(order_id)
    return render_template('orders/view.html', order=order)

@orders_bp.route('/<int:order_id>/edit')
def edit_order(order_id):
    """Edit an existing order."""
    order = Order.query.get_or_404(order_id)
    # For now, we'll just redirect to the order details
    # In a future implementation, we could pre-populate the wizard
    flash('Order editing will be implemented in a future update.', 'info')
    return redirect(url_for('orders.view_order', order_id=order_id))

@orders_bp.route('/<int:order_id>/delete', methods=['POST'])
def delete_order(order_id):
    """Delete an order."""
    order = Order.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()
    flash('Order deleted successfully!', 'success')
    return redirect(url_for('orders.list_orders'))

@orders_bp.route('/api/cost-preview', methods=['POST'])
def cost_preview():
    """API endpoint for live cost calculation."""
    data = request.json
    
    if not data or 'ingredients' not in data or 'packaging' not in data:
        return jsonify({'error': 'Invalid data format'}), 400
    
    # Calculate costs
    costs = calculate_order_cost_preview(data['ingredients'], data['packaging'])
    
    # Add per-cookie cost if quantity is provided
    if 'quantity' in data and data['quantity'] > 0:
        costs['cost_per_cookie_cents'] = round(costs['total_cost_cents'] / data['quantity'])
    else:
        costs['cost_per_cookie_cents'] = 0
    
    # Calculate margin if sale price is provided
    if 'sale_price_cents' in data and data['sale_price_cents'] > 0:
        costs['margin_cents'] = data['sale_price_cents'] - costs['total_cost_cents']
        costs['margin_percentage'] = round((costs['margin_cents'] / data['sale_price_cents']) * 100, 2)
    else:
        costs['margin_cents'] = 0
        costs['margin_percentage'] = 0
    
    return jsonify(costs)
