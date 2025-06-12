from flask import Blueprint, render_template
from models import db, Customer, Recipe, Order, Ingredient, Packaging, OrderIngredient, OrderPackaging
from cost_helpers import get_low_stock_items
from sqlalchemy import func
from datetime import datetime, timedelta
from sqlalchemy.sql import desc

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
def index():
    """Render the dashboard homepage with stats."""
    # Get counts for dashboard
    stats = {
        'customer_count': Customer.query.count(),
        'recipe_count': Recipe.query.count(),
        'order_count': Order.query.count(),
        'ingredient_count': Ingredient.query.count(),
        'packaging_count': Packaging.query.count()
    }
    
    # Get low stock items
    low_stock_ingredients, low_stock_packaging = get_low_stock_items()
    
    # Get financial stats for current period (last 30 days)
    today = datetime.now().date()
    thirty_days_ago = today - timedelta(days=30)
    sixty_days_ago = today - timedelta(days=60)
    
    # Current period stats (last 30 days)
    current_period_stats = db.session.query(
        func.sum(Order.sale_price_total_cents).label('revenue'),
        func.count(Order.id).label('order_count'),
        func.sum(Order.quantity_baked).label('cookies_baked')
    ).filter(
        Order.order_date >= thirty_days_ago
    ).first()
    
    # Previous period stats (30-60 days ago) for comparison
    previous_period_stats = db.session.query(
        func.sum(Order.sale_price_total_cents).label('revenue'),
        func.count(Order.id).label('order_count'),
        func.sum(Order.quantity_baked).label('cookies_baked')
    ).filter(
        Order.order_date >= sixty_days_ago,
        Order.order_date < thirty_days_ago
    ).first()
    
    # Calculate ingredient costs
    ingredient_costs_query = db.session.query(
        func.sum(OrderIngredient.cost_at_time_of_use_cents).label('ingredient_cost')
    ).join(Order, Order.id == OrderIngredient.order_id) \
     .filter(Order.order_date >= thirty_days_ago)
    
    # Calculate packaging costs
    packaging_costs_query = db.session.query(
        func.sum(OrderPackaging.cost_at_time_of_use_cents).label('packaging_cost')
    ).join(Order, Order.id == OrderPackaging.order_id) \
     .filter(Order.order_date >= thirty_days_ago)
    
    current_ingredient_costs = ingredient_costs_query.first()
    current_packaging_costs = packaging_costs_query.first()
    
    # Calculate previous period ingredient costs
    previous_ingredient_costs_query = db.session.query(
        func.sum(OrderIngredient.cost_at_time_of_use_cents).label('ingredient_cost')
    ).join(Order, Order.id == OrderIngredient.order_id) \
     .filter(
        Order.order_date >= sixty_days_ago,
        Order.order_date < thirty_days_ago
     )
    
    # Calculate previous period packaging costs
    previous_packaging_costs_query = db.session.query(
        func.sum(OrderPackaging.cost_at_time_of_use_cents).label('packaging_cost')
    ).join(Order, Order.id == OrderPackaging.order_id) \
     .filter(
        Order.order_date >= sixty_days_ago,
        Order.order_date < thirty_days_ago
     )
    
    previous_ingredient_costs = previous_ingredient_costs_query.first()
    previous_packaging_costs = previous_packaging_costs_query.first()
    
    # Dashboard metrics
    revenue = current_period_stats.revenue or 0
    order_count = current_period_stats.order_count or 0
    cookies_baked = current_period_stats.cookies_baked or 0
    
    # Cost and profit calculations
    ingredient_cost = current_ingredient_costs.ingredient_cost or 0
    packaging_cost = current_packaging_costs.packaging_cost or 0
    total_cost = ingredient_cost + packaging_cost
    profit = revenue - total_cost
    
    # Previous period values for comparison
    prev_revenue = previous_period_stats.revenue or 0
    prev_order_count = previous_period_stats.order_count or 0
    prev_cookies_baked = previous_period_stats.cookies_baked or 0
    
    prev_ingredient_cost = previous_ingredient_costs.ingredient_cost or 0
    prev_packaging_cost = previous_packaging_costs.packaging_cost or 0
    prev_total_cost = prev_ingredient_cost + prev_packaging_cost
    prev_profit = prev_revenue - prev_total_cost
    
    # Calculate percentage changes
    revenue_change = calculate_percentage_change(revenue, prev_revenue)
    profit_change = calculate_percentage_change(profit, prev_profit)
    order_change = calculate_percentage_change(order_count, prev_order_count)
    cookies_change = calculate_percentage_change(cookies_baked, prev_cookies_baked)
    
    # Get recent orders
    recent_orders = Order.query.order_by(Order.order_date.desc()).limit(5).all()
    
    dashboard_data = {
        'revenue_cents': revenue,
        'profit_cents': profit,
        'order_count': order_count,
        'cookies_baked': cookies_baked,
        'revenue_change': revenue_change,
        'profit_change': profit_change,
        'order_change': order_change,
        'cookies_change': cookies_change
    }
    
    return render_template(
        'dashboard.html',
        stats=stats,
        dashboard=dashboard_data,
        recent_orders=recent_orders,
        low_stock_ingredients=low_stock_ingredients,
        low_stock_packaging=low_stock_packaging
    )


def calculate_percentage_change(current, previous):
    """Calculate percentage change between two values."""
    if previous == 0:
        return 100 if current > 0 else 0
    
    return ((current - previous) / previous) * 100


@dashboard_bp.route('/hello')
def hello():
    """Simple hello world route for testing."""
    return "Hello, Cookie Manager!"
