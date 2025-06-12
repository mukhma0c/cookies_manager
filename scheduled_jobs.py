"""
Scheduled jobs for Cookie Manager application.
"""
from cost_helpers import get_low_stock_items
from flask import current_app

# Store Flask app instance
flask_app = None

def check_low_stock():
    """
    Check for low stock items and log them.
    In a future version, this could send email notifications.
    """
    global flask_app
    if not flask_app:
        return
        
    with flask_app.app_context():
        low_stock_ingredients, low_stock_packaging = get_low_stock_items()
        
        if low_stock_ingredients:
            flask_app.logger.warning(f"Low stock alert: {len(low_stock_ingredients)} ingredients below threshold")
            for item in low_stock_ingredients:
                flask_app.logger.warning(
                    f"Low stock: {item['item'].name} - {item['current_stock']} {item['unit']} "
                    f"(Threshold: {item['threshold']} {item['unit']})"
                )
        
        if low_stock_packaging:
            flask_app.logger.warning(f"Low stock alert: {len(low_stock_packaging)} packaging items below threshold")
            for item in low_stock_packaging:
                flask_app.logger.warning(
                    f"Low stock: {item['item'].name} - {item['current_stock']} {item['unit']} "
                    f"(Threshold: {item['threshold']} {item['unit']})"
                )

def register_jobs(scheduler, app):
    """
    Register all scheduled jobs.
    
    Args:
        scheduler: APScheduler instance
        app: Flask application instance
    """
    global flask_app
    flask_app = app
    # Check for low stock items every day at 8:00 AM
    scheduler.add_job(
        id='check_low_stock',
        func=check_low_stock,
        trigger='cron',
        hour=8,
        minute=0
    )
    
    # For development/testing, you can also add an interval job
    # that runs more frequently (e.g., every 10 minutes)
    scheduler.add_job(
        id='check_low_stock_interval',
        func=check_low_stock,
        trigger='interval',
        minutes=10
    )
