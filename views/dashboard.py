from flask import Blueprint, render_template

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
def index():
    """Render the dashboard homepage."""
    return render_template('dashboard.html')


@dashboard_bp.route('/hello')
def hello():
    """Simple hello world route for testing."""
    return "Hello, Cookie Manager!"
