#!/usr/bin/env python3

from app import app, db, Item

with app.app_context():
    print("🔍 Current database state:")
    print("=" * 50)

    # Get all items
    all_items = Item.query.all()
    print(f"Total items in database: {len(all_items)}")
    print()

    if all_items:
        print("Current items:")
        for item in all_items:
            print(f"  - {item.name} (ID: {item.id}, Quantity: {item.quantity}, Barcode: {item.barcode})")
    else:
        print("No items found in database")

    print()
    print("Looking for bread-related items:")
    bread_items = Item.query.filter(Item.name.ilike('%bread%')).all()
    if bread_items:
        for item in bread_items:
            print(f"  - {item.name} (ID: {item.id}, Quantity: {item.quantity})")
    else:
        print("  No bread items found")

    print()
    print("Recent backup files:")
    import os
    backup_dir = 'backups'
    if os.path.exists(backup_dir):
        backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.db')]
        if backup_files:
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: os.path.getmtime(os.path.join(backup_dir, x)), reverse=True)
            for i, backup_file in enumerate(backup_files[:5]):  # Show latest 5
                file_path = os.path.join(backup_dir, backup_file)
                size = os.path.getsize(file_path)
                mtime = os.path.getmtime(file_path)
                from datetime import datetime
                dt = datetime.fromtimestamp(mtime)
                print(f"  {i+1}. {backup_file} ({size} bytes, {dt.strftime('%Y-%m-%d %H:%M:%S')})")
        else:
            print("  No backup files found")
    else:
        print("  Backups directory does not exist")
