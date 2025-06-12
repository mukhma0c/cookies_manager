def register_blueprints(app):
    """
    Register all blueprints with the Flask app.
    
    Args:
        app (Flask): Flask application instance
    """
    from views.dashboard import dashboard_bp
    from views.orders import orders_bp
    from views.inventory import inventory_bp
    from views.purchases import purchases_bp
    from views.recipes import recipes_bp
    from views.reports import reports_bp
    from views.customers import customers_bp
    
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(purchases_bp)
    app.register_blueprint(recipes_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(customers_bp)
