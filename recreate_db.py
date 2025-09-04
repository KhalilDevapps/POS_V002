#!/usr/bin/env python3
"""
Script to recreate database tables with updated schema
"""

from app import create_tables, db
from flask import Flask

# Create Flask app context
app = Flask(__name__)
app.config['SECRET_KEY'] = 'temp-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    print("Dropping all tables...")
    db.drop_all()
    print("Creating all tables...")
    db.create_all()
    print("Creating default data...")
    create_tables()
    print("Database recreation completed successfully!")
