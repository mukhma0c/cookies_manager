from sqlalchemy import func
from models import db, Purchase, Ingredient, Packaging, OrderIngredient, OrderPackaging


def get_latest_unit_cost(item_type, item_id):
    """
    Get the latest unit cost for an ingredient or packaging item.
    
    Args:
        item_type (str): Either 'ingredient' or 'packaging'
        item_id (int): ID of the item
        
    Returns:
        int: Latest unit cost in cents, or None if no purchase exists
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
    unit_cost = get_latest_unit_cost('ingredient', ingredient_id)
    if unit_cost is None:
        # Fallback to default price if no purchase exists
        ingredient = Ingredient.query.get(ingredient_id)
        if ingredient and ingredient.default_price_per_unit_cents:
            unit_cost = ingredient.default_price_per_unit_cents
        else:
            return None
    
    return round(unit_cost * amount)


def calculate_packaging_cost(packaging_id, quantity):
    """
    Calculate cost for a specific quantity of packaging.
    
    Args:
        packaging_id (int): ID of the packaging
        quantity (float): Quantity to calculate cost for
        
    Returns:
        int: Cost in cents, or None if no price data exists
    """
    unit_cost = get_latest_unit_cost('packaging', packaging_id)
    if unit_cost is None:
        # Fallback to default price if no purchase exists
        packaging = Packaging.query.get(packaging_id)
        if packaging and packaging.default_price_per_unit_cents:
            unit_cost = packaging.default_price_per_unit_cents
        else:
            return None
    
    return round(unit_cost * quantity)


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
    # TODO: Implement calculation of current stock based on purchases and usage
    # For now, return empty lists
    return [], []
