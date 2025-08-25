from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Person(db.Model):
    """Model for storing detected/tracked persons"""
    __tablename__ = 'persons'
    
    id = db.Column(db.Integer, primary_key=True)
    track_id = db.Column(db.Integer, nullable=False)  # DeepSORT tracking ID
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    x = db.Column(db.Float, nullable=False)  # Bounding box coordinates
    y = db.Column(db.Float, nullable=False)
    width = db.Column(db.Float, nullable=False)
    height = db.Column(db.Float, nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    face_encoding = db.Column(db.Text, nullable=True)  # For face recognition
    session_id = db.Column(db.String(50), nullable=False)  # Tracking session
    
    def __repr__(self):
        return f'<Person {self.track_id} at {self.timestamp}>'

class TrackingSession(db.Model):
    """Model for tracking sessions"""
    __tablename__ = 'tracking_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(50), unique=True, nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    total_people_count = db.Column(db.Integer, default=0)
    current_people_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='active')  # active, stopped
    
    def __repr__(self):
        return f'<Session {self.session_id}>'

class PersonIdentity(db.Model):
    """Model for storing known person identities"""
    __tablename__ = 'person_identities'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    face_encoding = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Identity {self.name}>'
