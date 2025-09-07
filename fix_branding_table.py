#!/usr/bin/env python3
"""
Script to fix branding table - remove duplicates and add missing columns
"""
import sqlite3
import os

def fix_branding_table():
    """Fix the branding table by removing duplicates and adding missing columns"""
    db_path = 'instance/pos.db'

    if not os.path.exists(db_path):
        print("Database file not found!")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("=== CURRENT BRANDING TABLE STATUS ===")

        # Check current table structure
        cursor.execute("PRAGMA table_info(branding)")
        columns = cursor.fetchall()
        print(f"Current columns: {len(columns)}")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")

        # Count records
        cursor.execute("SELECT COUNT(*) FROM branding")
        count = cursor.fetchone()[0]
        print(f"Current records: {count}")

        if count > 1:
            print("\n=== REMOVING DUPLICATE RECORDS ===")
            # Keep the most recent record, delete others
            cursor.execute("""
                DELETE FROM branding
                WHERE id NOT IN (
                    SELECT MAX(id) FROM branding
                )
            """)
            deleted = cursor.rowcount
            print(f"Deleted {deleted} duplicate records")

        # Add missing columns
        print("\n=== ADDING MISSING COLUMNS ===")

        new_columns = [
            ('receipt_return_policy', 'VARCHAR(500)', "'For exchanges/returns, present this receipt within 30 days.'"),
            ('receipt_header_title', 'VARCHAR(100)', "'RECEIPT'"),
            ('receipt_number_label', 'VARCHAR(50)', "'Receipt #:'"),
            ('date_label', 'VARCHAR(50)', "'Date:'"),
            ('cashier_label', 'VARCHAR(50)', "'Cashier:'"),
            ('payment_method_label', 'VARCHAR(50)', "'Payment Method:'"),
            ('payment_method_value', 'VARCHAR(50)', "'Cash'"),
            ('cash_received_label', 'VARCHAR(50)', "'Cash Received:'"),
            ('change_label', 'VARCHAR(50)', "'Change:'"),
            ('currency_symbol', 'VARCHAR(10)', "'AFA'"),
            ('item_header', 'VARCHAR(50)', "'Item'"),
            ('quantity_header', 'VARCHAR(50)', "'Qty'"),
            ('amount_header', 'VARCHAR(50)', "'Amount'"),
            ('subtotal_label', 'VARCHAR(50)', "'Subtotal:'"),
            ('discount_label', 'VARCHAR(50)', "'Discount'"),
            ('total_label', 'VARCHAR(50)', "'TOTAL:'"),
            ('records_message', 'VARCHAR(200)', "'Please keep this receipt for your records.'"),
            ('powered_by_label', 'VARCHAR(50)', "'Powered by'"),
            ('version_text', 'VARCHAR(20)', "'v1.0'")
        ]

        existing_columns = [col[1] for col in columns]

        for col_name, col_type, default_value in new_columns:
            if col_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE branding ADD COLUMN {col_name} {col_type} DEFAULT {default_value}")
                    print(f"Added column: {col_name}")
                except Exception as e:
                    print(f"Error adding column {col_name}: {e}")

        # Update the single record with default values for new columns
        print("\n=== UPDATING RECORD WITH DEFAULT VALUES ===")
        update_sql = """
        UPDATE branding SET
            receipt_return_policy = 'For exchanges/returns, present this receipt within 30 days.',
            receipt_header_title = 'RECEIPT',
            receipt_number_label = 'Receipt #:',
            date_label = 'Date:',
            cashier_label = 'Cashier:',
            payment_method_label = 'Payment Method:',
            payment_method_value = 'Cash',
            cash_received_label = 'Cash Received:',
            change_label = 'Change:',
            currency_symbol = 'AFA',
            item_header = 'Item',
            quantity_header = 'Qty',
            amount_header = 'Amount',
            subtotal_label = 'Subtotal:',
            discount_label = 'Discount',
            total_label = 'TOTAL:',
            records_message = 'Please keep this receipt for your records.',
            powered_by_label = 'Powered by',
            version_text = 'v1.0'
        WHERE id = (SELECT MAX(id) FROM branding)
        """
        cursor.execute(update_sql)
        print("Updated record with default values")

        conn.commit()

        # Verify the fix
        print("\n=== VERIFICATION ===")
        cursor.execute("PRAGMA table_info(branding)")
        final_columns = cursor.fetchall()
        print(f"Final columns: {len(final_columns)}")

        cursor.execute("SELECT COUNT(*) FROM branding")
        final_count = cursor.fetchone()[0]
        print(f"Final records: {final_count}")

        # Show the final record
        cursor.execute("SELECT * FROM branding")
        record = cursor.fetchone()
        if record:
            print("\n=== FINAL RECORD ===")
            for i, col in enumerate(final_columns):
                if i < len(record):
                    value = record[i]
                    if value is None:
                        value = "NULL"
                    elif isinstance(value, str) and len(value) > 50:
                        value = value[:50] + "..."
                    print(f"{col[1]}: {value}")

        conn.close()
        print("\n✅ Branding table fixed successfully!")

    except Exception as e:
        print(f"❌ Error fixing branding table: {e}")

if __name__ == "__main__":
    fix_branding_table()
