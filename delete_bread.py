#!/usr/bin/env python3
"""
Script to delete the Bread item from the database
"""

from app import app, db, Item

with app.app_context():
    bread_item = Item.query.filter_by(name='Bread').first()

    if bread_item:
        print(f"Found Bread item: {bread_item.name} (Barcode: {bread_item.barcode})")
        db.session.delete(bread_item)
        db.session.commit()
        print("Bread item deleted successfully!")
    else:
        print("Bread item not found in database.")
