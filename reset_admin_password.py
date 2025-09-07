#!/usr/bin/env python3
"""
Admin Password Reset Script for POS System

This script allows administrators to reset the admin user password
from the command line without needing to access the web interface.

Usage:
    python reset_admin_password.py [new_password] [--username USERNAME]

Arguments:
    new_password    New password for the admin user (optional, will prompt if not provided)
    --username      Username to reset (default: admin)

Examples:
    python reset_admin_password.py
    python reset_admin_password.py mynewpassword
    python reset_admin_password.py securepass123 --username admin
"""

import os
import sys
import argparse
import getpass
from datetime import datetime, timezone

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def reset_admin_password():
    """Reset admin user password"""

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Reset admin user password for POS System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        'new_password',
        nargs='?',
        help='New password for the admin user'
    )

    parser.add_argument(
        '--username',
        default='admin',
        help='Username to reset (default: admin)'
    )

    parser.add_argument(
        '--confirm',
        action='store_true',
        help='Skip confirmation prompt'
    )

    args = parser.parse_args()

    # Import Flask and database components
    try:
        from flask import Flask
        from flask_sqlalchemy import SQLAlchemy
        from werkzeug.security import generate_password_hash
        from datetime import datetime, timezone
    except ImportError as e:
        print(f"❌ Error: Missing required packages. Please install dependencies:")
        print(f"   pip install flask flask-sqlalchemy werkzeug")
        print(f"   Error details: {e}")
        sys.exit(1)

    # Check if database exists
    db_path = 'instance/pos.db'
    if not os.path.exists(db_path):
        print(f"❌ Error: Database file not found at {db_path}")
        print("   Please ensure the POS system has been initialized.")
        sys.exit(1)

    # Get new password
    if args.new_password:
        new_password = args.new_password
    else:
        print("🔐 Password Reset Tool for POS System")
        print("=" * 40)
        new_password = getpass.getpass("Enter new password: ")
        confirm_password = getpass.getpass("Confirm new password: ")

        if new_password != confirm_password:
            print("❌ Error: Passwords do not match!")
            sys.exit(1)

    # Validate password strength
    if len(new_password) < 6:
        print("❌ Error: Password must be at least 6 characters long!")
        sys.exit(1)

    # Confirm action
    if not args.confirm:
        print(f"\n⚠️  WARNING: This will reset the password for user '{args.username}'")
        print("   Make sure you have the correct username!")
        confirm = input("Continue? (y/N): ").lower().strip()
        if confirm not in ['y', 'yes']:
            print("❌ Operation cancelled.")
            sys.exit(0)

    # Import the Flask app and models from the main application
    try:
        # Try to import from the main app.py file
        # Add current directory to Python path if not already there
        if os.getcwd() not in sys.path:
            sys.path.insert(0, os.getcwd())

        from app import app, db, User, create_tables

        with app.app_context():
            # Ensure tables exist
            create_tables()

            # Find the user
            user = User.query.filter_by(username=args.username).first()

            if not user:
                print(f"❌ Error: User '{args.username}' not found in database!")
                print("   Available users:")
                users = User.query.all()
                for u in users:
                    print(f"     - {u.username} (Role: {u.role})")
                sys.exit(1)

            # Store old password hash for logging
            old_hash = user.password_hash[:10] + "..."  # Partial hash for logging

            # Reset password
            user.set_password(new_password)

            # Update timestamp
            user.created_at = datetime.now(timezone.utc)

            db.session.commit()

            print("✅ SUCCESS: Password reset completed!")
            print(f"   User: {user.username}")
            print(f"   Role: {user.role}")
            print(f"   New Password: {'*' * len(new_password)}")
            print(f"   Reset Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            # Security recommendations
            print("\n🔒 SECURITY RECOMMENDATIONS:")
            print("   • Change this password after first login")
            print("   • Use a strong, unique password")
            print("   • Store passwords securely")
            print("   • Consider enabling two-factor authentication")

            print("\n🚀 You can now login with the new password!")

    except Exception as e:
        print(f"❌ Error: Failed to reset password!")
        print(f"   Details: {str(e)}")
        print("   Please check database permissions and try again.")
        sys.exit(1)

def show_help():
    """Show help information"""
    print(__doc__)

def main():
    """Main function"""
    if len(sys.argv) == 1:
        # No arguments provided, show interactive mode
        reset_admin_password()
    elif sys.argv[1] in ['-h', '--help', 'help']:
        show_help()
    else:
        # Parse arguments normally
        reset_admin_password()

if __name__ == '__main__':
    main()
