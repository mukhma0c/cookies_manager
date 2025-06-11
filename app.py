import os
from flask import Flask, send_from_directory, session
from flask_migrate import Migrate
from models import db
from config import config
from datetime import timedelta


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
    
    # Configure session
    app.permanent_session_lifetime = timedelta(days=1)
    
    # Initialize extensions
    db.init_app(app)
    Migrate(app, db)
    
    # Register blueprints
    from views import register_blueprints
    register_blueprints(app)
    
    # Serve static files
    @app.route('/static/<path:filename>')
    def static_files(filename):
        return send_from_directory(os.path.join(app.root_path, 'static'), filename)
    
    # Add Jinja2 filters
    @app.template_filter('nl2br')
    def nl2br_filter(text):
        if not text:
            return ''
        return text.replace('\n', '<br>')
    
    # Add template context processor for current date
    @app.context_processor
    def utility_processor():
        from datetime import datetime
        return {'now': datetime.utcnow}
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5001)
