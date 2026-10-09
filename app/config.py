# Configuration file for Brain Tumor Detection Web Application
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Application configuration settings."""
    # Secrets (SECRET_KEY) come from environment variables, never hardcoded in production
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-dev-secret-key-change-in-production')
    
    # SQLite Database setup
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 
        f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload folder configuration
    UPLOAD_FOLDER = os.environ.get(
        'UPLOAD_FOLDER',
        os.path.join(os.path.dirname(BASE_DIR), 'uploads')
    )
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB upload limit
    
    # YOLO Model configuration
    MODEL_PATH = os.environ.get(
        'MODEL_PATH',
        os.path.join(os.path.dirname(BASE_DIR), 'models', 'best.pt')
    )
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'dcm'}
