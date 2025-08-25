from flask_sqlalchemy import SQLAlchemy
from models import db

def init_db(app):
    """Initialize database with Flask app"""
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        print("Database initialized successfully!")

def get_db():
    """Get database instance"""
    return db
