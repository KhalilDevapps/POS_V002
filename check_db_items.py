#!/usr/bin/env python3
"""
Script to check items in the database
"""

from app import app, db, Item

with app.app_context():
    items = Item.query.all()
    print(f"Total items in database: {len(items)}")

    if items:
        print("\nItems found:")
        for item in items:
            print(f"- {item.name} (Barcode: {item.barcode}, Quantity: {item.quantity}, Price: {item.selling_price})")
    else:
        print("No items found in database.")
