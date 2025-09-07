import sqlite3

def add_receipt_policy_column():
    conn = sqlite3.connect('pos.db')
    cursor = conn.cursor()

    # Add receipt_return_policy column to branding table
    cursor.execute('PRAGMA table_info(branding)')
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]

    if 'receipt_return_policy' not in column_names:
        print('Adding receipt_return_policy column to branding table...')
        cursor.execute('ALTER TABLE branding ADD COLUMN receipt_return_policy VARCHAR(500) DEFAULT "For exchanges/returns, present this receipt within 30 days."')
        conn.commit()

    conn.close()
    print('Database updated successfully!')

if __name__ == '__main__':
    add_receipt_policy_column()
