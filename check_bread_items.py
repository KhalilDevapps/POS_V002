#!/usr/bin/env python3

from app import app, db, Item

with app.app_context():
    # Find bread-related items
    bread_items = Item.query.filter(Item.name.ilike('%bread%')).all()

    print(f"Found {len(bread_items)} bread-related items:")
    for item in bread_items:
        print(f"- {item.name} (ID: {item.id}, Quantity: {item.quantity})")

    # If no bread items found, let's add one for testing
    if not bread_items:
        print("\nNo bread items found. Adding a test 'Bread' item...")

        # Generate unique barcode
        import datetime
        from datetime import timezone
        barcode = str(int(datetime.datetime.now(timezone.utc).timestamp() * 1000000))

        bread_item = Item(
            name="Bread",
            buying_price=25.00,
            selling_price=40.00,
            quantity=80,
            barcode=barcode
        )

        db.session.add(bread_item)
        db.session.commit()

        print(f"Added test item: {bread_item.name} (ID: {bread_item.id}, Barcode: {bread_item.barcode})")
