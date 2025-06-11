import os
from flask import Flask
from flask_migrate import Migrate
from models import db
from config import config


def create_app(config_name=None):
    """
    Create and configure the Flask application.
    
    Args:
        config_name (str): Configuration to use. Defaults to the value of the
                          FLASK_CONFIG environment variable or 'default' if not set.
    
    Returns:
        Flask: Configured Flask application
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    Migrate(app, db)
    
    # Register blueprints
    from views import register_blueprints
    register_blueprints(app)
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
