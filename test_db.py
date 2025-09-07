#!/usr/bin/env python3
import sqlite3
import os

def test_database():
    db_path = 'instance/pos.db'

    print(f"Database path: {db_path}")
    print(f"Database exists: {os.path.exists(db_path)}")

    if os.path.exists(db_path):
        print(f"Database size: {os.path.getsize(db_path)} bytes")

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Check users table
            cursor.execute('SELECT id, username, role FROM users')
            users = cursor.fetchall()

            print(f"\nUsers in database ({len(users)}):")
            for user in users:
                print(f"  ID: {user[0]}, Username: {user[1]}, Role: {user[2]}")

            # Check if users table has password_hash column
            cursor.execute('PRAGMA table_info(users)')
            columns = cursor.fetchall()
            print("\nUsers table columns:")
            for col in columns:
                print(f"  {col[1]} ({col[2]})")

            conn.close()
            print("\n✅ Database connection successful!")

        except Exception as e:
            print(f"\n❌ Database error: {e}")
    else:
        print("❌ Database file not found!")

if __name__ == '__main__':
    test_database()
