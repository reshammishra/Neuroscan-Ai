import os
from urllib.parse import urlsplit
from flask import Flask, redirect, render_template, request, session, url_for
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

from .config import Config
from .models import db, User
from .ui_translations import UI_TRANSLATIONS

csrf = CSRFProtect()
login_manager = LoginManager()

def create_app(config_class=Config):
    """
    Application factory pattern for creating Flask app instance.
    Initializes database, login management, CSRF protection, and blueprints.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    def current_language():
        return session.get('language', 'en')

    def translate(text):
        if current_language() == 'hi':
            return UI_TRANSLATIONS.get(text, text)
        return text

    app.jinja_env.globals.update(t=translate, current_language=current_language)

    @app.route('/language', methods=['POST'])
    def set_language():
        language = request.form.get('language', 'en')
        if language not in {'en', 'hi'}:
            language = 'en'
        session['language'] = language

        referrer = request.referrer
        if referrer and urlsplit(referrer).netloc == request.host:
            return redirect(referrer)
        return redirect(url_for('detect.index'))

    # Ensure uploads folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)

    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from .blueprints.auth import auth_bp
    from .blueprints.detect import detect_bp
    from .blueprints.history import history_bp
    from .blueprints.report import report_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(detect_bp, url_prefix='')  # Contains / and /detect
    app.register_blueprint(history_bp, url_prefix='/history')
    app.register_blueprint(report_bp, url_prefix='/report')

    # Create tables automatically for SQLite
    with app.app_context():
        db.create_all()

    # Generic error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404

    @app.errorhandler(413)
    def request_entity_too_large(error):
        return render_template('413.html'), 413

    return app
