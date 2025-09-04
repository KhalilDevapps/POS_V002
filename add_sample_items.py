#!/usr/bin/env python3
"""
Script to add sample items to the database
"""

from app import app, db, Item
from datetime import datetime, timezone

sample_items = [
    {'name': 'Apple', 'buy': 50, 'sell': 80, 'qty': 100},
    {'name': 'Banana', 'buy': 30, 'sell': 50, 'qty': 150},
    {'name': 'Orange', 'buy': 40, 'sell': 70, 'qty': 120},
    {'name': 'Milk 1L', 'buy': 120, 'sell': 150, 'qty': 50},
    {'name': 'Bread', 'buy': 25, 'sell': 40, 'qty': 80},
    {'name': 'Rice 1kg', 'buy': 80, 'sell': 110, 'qty': 60},
    {'name': 'Chicken 1kg', 'buy': 200, 'sell': 280, 'qty': 30},
    {'name': 'Eggs (12)', 'buy': 60, 'sell': 90, 'qty': 40},
    {'name': 'Sugar 1kg', 'buy': 70, 'sell': 95, 'qty': 70},
    {'name': 'Tea 100g', 'buy': 150, 'sell': 200, 'qty': 25}
]

with app.app_context():
    added_count = 0
    for item_data in sample_items:
        # Check if item already exists
        existing = Item.query.filter_by(name=item_data['name']).first()
        if not existing:
            barcode = str(int(datetime.now(timezone.utc).timestamp() * 1000000) + added_count)
            item = Item(
                name=item_data['name'],
                buying_price=item_data['buy'],
                selling_price=item_data['sell'],
                quantity=item_data['qty'],
                barcode=barcode
            )
            db.session.add(item)
            added_count += 1

    db.session.commit()
    print(f"Added {added_count} sample items to the database.")
