#!/usr/bin/env python3
"""
Database Check Script
Verify database state and user creation
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    secret_question = db.Column(db.String(200), nullable=True)
    secret_answer = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

def check_database():
    """Check database state and users"""
    print("🔍 Checking Database State...")
    print("=" * 40)

    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        print("✅ Database tables created/verified")

        # Check existing users
        users = User.query.all()
        print(f"📊 Found {len(users)} users in database:")

        for user in users:
            print(f"   - ID: {user.id}")
            print(f"     Username: {user.username}")
            print(f"     Role: {user.role}")
            print(f"     Created: {user.created_at}")
            print(f"     Has Password: {'Yes' if user.password_hash else 'No'}")
            print()

        # Create default users if they don't exist
        if not User.query.filter_by(username='admin').first():
            print("👤 Creating default admin user...")
            admin = User(username='admin', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            print("✅ Admin user created")

        if not User.query.filter_by(username='cashier').first():
            print("👤 Creating default cashier user...")
            cashier = User(username='cashier', role='cashier')
            cashier.set_password('cashier123')
            db.session.add(cashier)
            print("✅ Cashier user created")

        db.session.commit()

        # Verify users after creation
        users = User.query.all()
        print(f"\n📊 Final user count: {len(users)}")
        for user in users:
            print(f"   - {user.username} ({user.role})")

        # Test password verification
        print("\n🔐 Testing Password Verification:")
        admin_user = User.query.filter_by(username='admin').first()
        cashier_user = User.query.filter_by(username='cashier').first()

        if admin_user:
            admin_check = admin_user.check_password('admin123')
            print(f"   Admin password check: {'✅ PASS' if admin_check else '❌ FAIL'}")

        if cashier_user:
            cashier_check = cashier_user.check_password('cashier123')
            print(f"   Cashier password check: {'✅ PASS' if cashier_check else '❌ FAIL'}")

    print("\n" + "=" * 40)
    print("🎉 Database check completed!")

if __name__ == "__main__":
    check_database()
