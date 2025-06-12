from sqlalchemy import func
from models import db, Purchase, Ingredient, Packaging, OrderIngredient, OrderPackaging


def get_latest_unit_cost(item_type, item_id):
    """
    Get the latest unit cost for an ingredient or packaging item.
    
    Args:
        item_type (str): Either 'ingredient' or 'packaging'
        item_id (int): ID of the item
        
    Returns:
        int: Latest unit cost in millicents, or None if no purchase exists
            (Note: 1 cent = 1000 millicents)
    """
    latest_purchase = Purchase.query.filter_by(
        item_type=item_type,
        item_id=item_id
    ).order_by(Purchase.purchase_date.desc()).first()
    
    return latest_purchase.unit_cost_cents if latest_purchase else None


def calculate_ingredient_cost(ingredient_id, amount):
    """
    Calculate cost for a specific amount of an ingredient.
    
    Args:
        ingredient_id (int): ID of the ingredient
        amount (float): Amount to calculate cost for
        
    Returns:
        int: Cost in cents, or None if no price data exists
    """
    unit_cost_millicents = get_latest_unit_cost('ingredient', ingredient_id)
    if unit_cost_millicents is None:
        # Fallback to default price if no purchase exists
        ingredient = Ingredient.query.get(ingredient_id)
        if ingredient and ingredient.default_price_per_unit_cents:
            # Convert default price (cents) to millicents for consistent calculation
            unit_cost_millicents = ingredient.default_price_per_unit_cents * 1000
        else:
            return None
    
    # Calculate cost in millicents, then convert back to cents
    return int((unit_cost_millicents * amount) / 1000)


def calculate_packaging_cost(packaging_id, quantity):
    """
    Calculate cost for a specific quantity of packaging.
    
    Args:
        packaging_id (int): ID of the packaging
        quantity (float): Quantity to calculate cost for
        
    Returns:
        int: Cost in cents, or None if no price data exists
    """
    unit_cost_millicents = get_latest_unit_cost('packaging', packaging_id)
    if unit_cost_millicents is None:
        # Fallback to default price if no purchase exists
        packaging = Packaging.query.get(packaging_id)
        if packaging and packaging.default_price_per_unit_cents:
            # Convert default price (cents) to millicents for consistent calculation
            unit_cost_millicents = packaging.default_price_per_unit_cents * 1000
        else:
            return None
    
    # Calculate cost in millicents, then convert back to cents
    return int((unit_cost_millicents * quantity) / 1000)


def calculate_order_cost_preview(ingredients, packaging):
    """
    Calculate a preview of order costs based on current prices.
    
    Args:
        ingredients (list): List of dicts with 'id' and 'amount' keys
        packaging (list): List of dicts with 'id' and 'quantity' keys
        
    Returns:
        dict: Dict with ingredient_cost_cents, packaging_cost_cents, total_cost_cents
    """
    ingredient_cost_cents = 0
    packaging_cost_cents = 0
    
    # Calculate ingredient costs
    for item in ingredients:
        cost = calculate_ingredient_cost(item['id'], item['amount'])
        if cost:
            ingredient_cost_cents += cost
    
    # Calculate packaging costs
    for item in packaging:
        cost = calculate_packaging_cost(item['id'], item['quantity'])
        if cost:
            packaging_cost_cents += cost
    
    total_cost_cents = ingredient_cost_cents + packaging_cost_cents
    
    return {
        'ingredient_cost_cents': ingredient_cost_cents,
        'packaging_cost_cents': packaging_cost_cents,
        'total_cost_cents': total_cost_cents
    }


def snapshot_order_costs(order, ingredients, packaging):
    """
    Create cost snapshots for an order's ingredients and packaging.
    
    Args:
        order (Order): Order object
        ingredients (list): List of dicts with 'id' and 'amount' keys
        packaging (list): List of dicts with 'id' and 'quantity' keys
        
    Returns:
        None
    """
    # Create ingredient snapshots
    for item in ingredients:
        ingredient_id = item['id']
        amount = item['amount']
        cost = calculate_ingredient_cost(ingredient_id, amount)
        
        if cost is None:
            # Default to 0 if no cost data
            cost = 0
        
        order_ingredient = OrderIngredient(
            order_id=order.id,
            ingredient_id=ingredient_id,
            amount_used=amount,
            cost_at_time_of_use_cents=cost
        )
        db.session.add(order_ingredient)
    
    # Create packaging snapshots
    for item in packaging:
        packaging_id = item['id']
        quantity = item['quantity']
        cost = calculate_packaging_cost(packaging_id, quantity)
        
        if cost is None:
            # Default to 0 if no cost data
            cost = 0
        
        order_packaging = OrderPackaging(
            order_id=order.id,
            packaging_id=packaging_id,
            quantity_used=quantity,
            cost_at_time_of_use_cents=cost
        )
        db.session.add(order_packaging)
    
    db.session.commit()


def get_low_stock_items():
    """
    Get items that are below their low stock threshold.
    
    Returns:
        tuple: Two lists - low stock ingredients and low stock packaging
    """
    from sqlalchemy import func
    from models import Purchase, OrderIngredient, OrderPackaging, Ingredient, Packaging
    
    # Calculate current stock levels for ingredients
    low_stock_ingredients = []
    
    # For each ingredient
    for ingredient in Ingredient.query.all():
        # Skip if no threshold is set
        if not ingredient.low_stock_threshold or ingredient.low_stock_threshold <= 0:
            continue
            
        # Total purchased
        total_purchased = db.session.query(func.sum(Purchase.quantity)).filter(
            Purchase.item_type == 'ingredient',
            Purchase.item_id == ingredient.id
        ).scalar() or 0
        
        # Total used in orders
        total_used = db.session.query(func.sum(OrderIngredient.amount_used)).filter(
            OrderIngredient.ingredient_id == ingredient.id
        ).scalar() or 0
        
        # Current stock level
        current_stock = total_purchased - total_used
        
        # Check if below threshold
        if current_stock <= ingredient.low_stock_threshold:
            low_stock_ingredients.append({
                'item': ingredient,
                'current_stock': current_stock,
                'threshold': ingredient.low_stock_threshold,
                'unit': ingredient.default_unit
            })
    
    # Calculate current stock levels for packaging
    low_stock_packaging = []
    
    # For each packaging item
    for packaging in Packaging.query.all():
        # Skip if no threshold is set
        if not packaging.low_stock_threshold or packaging.low_stock_threshold <= 0:
            continue
            
        # Total purchased
        total_purchased = db.session.query(func.sum(Purchase.quantity)).filter(
            Purchase.item_type == 'packaging',
            Purchase.item_id == packaging.id
        ).scalar() or 0
        
        # Total used in orders
        total_used = db.session.query(func.sum(OrderPackaging.quantity_used)).filter(
            OrderPackaging.packaging_id == packaging.id
        ).scalar() or 0
        
        # Current stock level
        current_stock = total_purchased - total_used
        
        # Check if below threshold
        if current_stock <= packaging.low_stock_threshold:
            low_stock_packaging.append({
                'item': packaging,
                'current_stock': current_stock,
                'threshold': packaging.low_stock_threshold,
                'unit': packaging.default_unit
            })
    
    return low_stock_ingredients, low_stock_packaging
