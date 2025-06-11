def register_blueprints(app):
    """
    Register all blueprints with the Flask app.
    
    Args:
        app (Flask): Flask application instance
    """
    from views.dashboard import dashboard_bp
    
    app.register_blueprint(dashboard_bp)
