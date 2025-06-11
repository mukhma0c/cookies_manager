from flask import Blueprint, render_template
from models import Customer, Recipe, Order, Ingredient, Packaging
from cost_helpers import get_low_stock_items

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
    
    return render_template(
        'dashboard.html',
        stats=stats,
        low_stock_ingredients=low_stock_ingredients,
        low_stock_packaging=low_stock_packaging
    )


@dashboard_bp.route('/hello')
def hello():
    """Simple hello world route for testing."""
    return "Hello, Cookie Manager!"
