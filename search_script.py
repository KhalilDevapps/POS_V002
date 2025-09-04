#!/usr/bin/env python3
"""
Standalone search script for POS items
"""

from app import app, db, Item
import sys

def search_items(query, search_type='name'):
    """
    Search items in the database

    Args:
        query (str): Search query
        search_type (str): Type of search ('name', 'barcode', 'all')

    Returns:
        list: List of matching items
    """
    with app.app_context():
        if not query:
            return []

        query = query.lower().strip()

        if search_type == 'name':
            # Search by item name (partial match)
            items = Item.query.filter(Item.name.ilike(f'%{query}%')).all()
        elif search_type == 'barcode':
            # Search by barcode (exact match or partial)
            items = Item.query.filter(Item.barcode.ilike(f'%{query}%')).all()
        elif search_type == 'all':
            # Search in both name and barcode
            items = Item.query.filter(
                db.or_(
                    Item.name.ilike(f'%{query}%'),
                    Item.barcode.ilike(f'%{query}%')
                )
            ).all()
        else:
            items = []

        return items

def display_results(items, query=""):
    """Display search results in a formatted way"""
    if not items:
        print(f"\nNo items found matching '{query}'")
        return

    print(f"\nFound {len(items)} item(s) matching '{query}':")
    print("-" * 80)
    print(f"{'Name':<20} {'Barcode':<18} {'Price':<8} {'Qty':<5} {'Status'}")
    print("-" * 80)

    for item in items:
        status = item.status
        print(f"{item.name:<20} {item.barcode:<18} {item.selling_price:<8.0f} {item.quantity:<5} {status}")

    print("-" * 80)

def main():
    """Main function for command line usage"""
    if len(sys.argv) < 2:
        print("Usage: python search_script.py <query> [search_type]")
        print("Search types: name, barcode, all (default: name)")
        print("\nExamples:")
        print("  python search_script.py apple")
        print("  python search_script.py 1756987078934193 barcode")
        print("  python search_script.py milk all")
        return

    query = sys.argv[1]
    search_type = sys.argv[2] if len(sys.argv) > 2 else 'name'

    if search_type not in ['name', 'barcode', 'all']:
        print("Invalid search type. Use: name, barcode, or all")
        return

    print(f"Searching for '{query}' in {search_type}...")
    items = search_items(query, search_type)
    display_results(items, query)

if __name__ == '__main__':
    main()
