#!/usr/bin/env python3
"""
Script to check branding table contents
"""
import sqlite3
import os

def check_branding_table():
    """Check what records exist in the branding table"""
    db_path = 'instance/pos.db'

    if not os.path.exists(db_path):
        print("Database file not found!")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if branding table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='branding'")
        if not cursor.fetchone():
            print("Branding table does not exist!")
            return

        # Get table structure
        print("=== BRANDING TABLE STRUCTURE ===")
        cursor.execute("PRAGMA table_info(branding)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"Column {col[0]}: {col[1]} ({col[2]})")

        print("\n=== BRANDING TABLE RECORDS ===")
        # Get all records
        cursor.execute("SELECT * FROM branding")
        records = cursor.fetchall()

        if not records:
            print("No records found in branding table")
        else:
            print(f"Found {len(records)} record(s):")
            for i, record in enumerate(records):
                print(f"\n--- Record {i+1} ---")
                for j, col in enumerate(columns):
                    if j < len(record):
                        value = record[j]
                        if value is None:
                            value = "NULL"
                        elif isinstance(value, str) and len(value) > 50:
                            value = value[:50] + "..."
                        print(f"{col[1]}: {value}")

        conn.close()

    except Exception as e:
        print(f"Error checking branding table: {e}")

if __name__ == "__main__":
    check_branding_table()
