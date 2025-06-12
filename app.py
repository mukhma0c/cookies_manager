import os
import click
from flask import Flask, send_from_directory, session
from flask_migrate import Migrate
from flask_apscheduler import APScheduler
from models import db
from config import config
from datetime import timedelta

# Initialize scheduler
scheduler = APScheduler()


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
    
    # Initialize and configure APScheduler
    scheduler.init_app(app)
    scheduler.start()
    
    # Register scheduled jobs
    from scheduled_jobs import register_jobs
    register_jobs(scheduler, app)
    
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
    
    # Add CLI command for initializing the database without seed data
    @app.cli.command('init-db')
    def init_db_command():
        """Initialize the database with schema but no seed data."""
        click.echo('Initializing the database schema...')
        # This will apply all migrations to create the schema
        from flask_migrate import upgrade
        upgrade()
        click.echo('Database schema initialized successfully.')
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5001)
