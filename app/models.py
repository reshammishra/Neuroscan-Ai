from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """
    User model representing registered users (Doctors and Students).
    Inherits from UserMixin to support Flask-Login session management.
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # 'doctor' or 'student'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to user's scans
    scans = db.relationship('Scan', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        """Hash and save user password using werkzeug."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    @property
    def is_doctor(self):
        """Helper to quickly check if user is a doctor."""
        return self.role.lower() == 'doctor'


class Scan(db.Model):
    """
    Scan model recording each processed medical scan.
    Belongs to a specific user for strict per-user access control.
    """
    __tablename__ = 'scans'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(10), nullable=False)  # 'jpg', 'png', 'dcm'
    
    # Detection metrics
    predicted_class = db.Column(db.String(64), nullable=False)
    confidence = db.Column(db.Float, nullable=False)  # Stored as percentage or float (0-100)
    tumor_area_percent = db.Column(db.Float, nullable=True)  # Estimated relative area %
    tumor_size_mm = db.Column(db.String(64), nullable=True)  # Estimated physical dimensions if DICOM pixel spacing is available
    
    # Stored image file paths (relative to uploads directory)
    annotated_image_path = db.Column(db.String(255), nullable=True)
    heatmap_image_path = db.Column(db.String(255), nullable=True)
    
    # Doctor clinical notes (only editable/visible for doctors)
    clinical_notes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
