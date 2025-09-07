#!/usr/bin/env python3

from app import app, db, Item

with app.app_context():
    # Find the bread item
    bread_item = Item.query.filter_by(name="Bread").first()

    if bread_item:
        print(f"Found bread item: {bread_item.name} (ID: {bread_item.id}, Quantity: {bread_item.quantity})")

        # Delete the item
        db.session.delete(bread_item)
        db.session.commit()

        print(f"✅ Successfully deleted bread item: {bread_item.name}")

        # Verify deletion
        remaining_bread = Item.query.filter_by(name="Bread").first()
        if remaining_bread:
            print(f"❌ Error: Bread item still exists after deletion!")
        else:
            print("✅ Verified: Bread item successfully deleted from database")
    else:
        print("❌ No bread item found to delete")
