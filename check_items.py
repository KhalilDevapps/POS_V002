from app import db, Item, create_tables
import os

# Set up Flask app context
os.environ['FLASK_APP'] = 'app.py'

# Create tables if they don't exist
create_tables()

# Check items
with db.session.begin():
    items = Item.query.all()
    print(f"Total items in database: {len(items)}")
    if items:
        for item in items[:5]:  # Show first 5 items
            print(f"ID: {item.id}, Name: {item.name}, Barcode: {item.barcode}")
    else:
        print("No items found. Adding sample items...")

        # Add sample items
        sample_items = [
            {'name': 'Apple', 'buy': 50, 'sell': 80, 'qty': 100},
            {'name': 'Banana', 'buy': 30, 'sell': 50, 'qty': 150},
        ]

        for item_data in sample_items:
            from datetime import datetime, timezone
            barcode = str(int(datetime.now(timezone.utc).timestamp() * 1000000))
            item = Item(
                name=item_data['name'],
                buying_price=item_data['buy'],
                selling_price=item_data['sell'],
                quantity=item_data['qty'],
                barcode=barcode
            )
            db.session.add(item)

        db.session.commit()
        print("Sample items added successfully!")
