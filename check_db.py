import sqlite3

def check_database():
    conn = sqlite3.connect('instance/pos.db')
    cursor = conn.cursor()

    # Check all tables
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
    tables = cursor.fetchall()
    print('Database tables:')
    for table in tables:
        print(f'  {table[0]}')

    # Check item table
    cursor.execute('PRAGMA table_info(item)')
    item_columns = cursor.fetchall()
    print('\nItem table columns:')
    for col in item_columns:
        print(f'  {col[1]} - {col[2]}')

    # Check category table
    cursor.execute('PRAGMA table_info(category)')
    category_columns = cursor.fetchall()
    print('\nCategory table columns:')
    for col in category_columns:
        print(f'  {col[1]} - {col[2]}')

    conn.close()

if __name__ == '__main__':
    check_database()
