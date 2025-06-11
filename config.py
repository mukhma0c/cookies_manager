import os
from pathlib import Path

basedir = Path(__file__).parent


class Config:
    """Base configuration settings."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-please-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{Path(basedir) / "instance" / "db.sqlite3"}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = Path(basedir) / 'static' / 'img'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    

class DevelopmentConfig(Config):
    """Development configuration settings."""
    DEBUG = True


class TestingConfig(Config):
    """Testing configuration settings."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production configuration settings."""
    DEBUG = False
    # In production, set SECRET_KEY as environment variable


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
