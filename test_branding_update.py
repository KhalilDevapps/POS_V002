#!/usr/bin/env python3
"""
Script to test branding updates via CLI
"""
import sqlite3
import os

def test_branding_update():
    """Test updating branding fields and verify they persist"""
    db_path = 'instance/pos.db'

    if not os.path.exists(db_path):
        print("Database file not found!")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("=== BEFORE UPDATE ===")
        cursor.execute("SELECT app_name, footer_text, currency_symbol, receipt_return_policy FROM branding WHERE id = (SELECT MAX(id) FROM branding)")
        before = cursor.fetchone()
        print(f"App Name: {before[0]}")
        print(f"Footer Text: {before[1]}")
        print(f"Currency Symbol: {before[2]}")
        print(f"Return Policy: {before[3][:50]}...")

        print("\n=== UPDATING BRANDING FIELDS ===")

        # Update some branding fields
        update_sql = """
        UPDATE branding SET
            app_name = 'My Custom POS',
            footer_text = 'Thank you for choosing our store!',
            currency_symbol = 'USD',
            receipt_return_policy = 'Returns accepted within 14 days with receipt.',
            business_name = 'Tech Solutions Inc.',
            payment_method_value = 'Card',
            total_label = 'GRAND TOTAL:'
        WHERE id = (SELECT MAX(id) FROM branding)
        """

        cursor.execute(update_sql)
        conn.commit()

        print("✅ Branding fields updated successfully!")

        print("\n=== AFTER UPDATE ===")
        cursor.execute("SELECT app_name, footer_text, currency_symbol, receipt_return_policy, business_name, payment_method_value, total_label FROM branding WHERE id = (SELECT MAX(id) FROM branding)")
        after = cursor.fetchone()
        print(f"App Name: {after[0]}")
        print(f"Footer Text: {after[1]}")
        print(f"Currency Symbol: {after[2]}")
        print(f"Return Policy: {after[3]}")
        print(f"Business Name: {after[4]}")
        print(f"Payment Method: {after[5]}")
        print(f"Total Label: {after[6]}")

        # Test that the changes persist after reconnecting
        print("\n=== TESTING PERSISTENCE ===")
        conn.close()

        # Reconnect and verify
        conn2 = sqlite3.connect(db_path)
        cursor2 = conn2.cursor()
        cursor2.execute("SELECT app_name, footer_text, currency_symbol FROM branding WHERE id = (SELECT MAX(id) FROM branding)")
        persisted = cursor2.fetchone()
        print(f"Persisted App Name: {persisted[0]}")
        print(f"Persisted Footer Text: {persisted[1]}")
        print(f"Persisted Currency Symbol: {persisted[2]}")

        if persisted[0] == 'My Custom POS' and persisted[1] == 'Thank you for choosing our store!' and persisted[2] == 'USD':
            print("✅ Changes persisted successfully!")
        else:
            print("❌ Changes did not persist!")

        conn2.close()

    except Exception as e:
        print(f"❌ Error testing branding update: {e}")

if __name__ == "__main__":
    test_branding_update()
