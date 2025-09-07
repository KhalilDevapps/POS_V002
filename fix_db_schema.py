import sqlite3

def fix_database_schema():
    conn = sqlite3.connect('pos.db')
    cursor = conn.cursor()

    # Add category_id column if missing
    cursor.execute('PRAGMA table_info(item)')
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]

    if 'category_id' not in column_names:
        print('Adding category_id column to root pos.db...')
        cursor.execute('ALTER TABLE item ADD COLUMN category_id INTEGER REFERENCES category(id)')
        conn.commit()

    if 'expiry_date' not in column_names:
        print('Adding expiry_date column to root pos.db...')
        cursor.execute('ALTER TABLE item ADD COLUMN expiry_date DATE')
        conn.commit()

    # Check if category table exists
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="category"')
    if not cursor.fetchone():
        print('Creating category table...')
        cursor.execute('''
            CREATE TABLE category (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                description VARCHAR(200),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

    # Check if other required tables exist
    required_tables = ['user', 'sale', 'sale_item', 'branding', 'activity_log']
    for table in required_tables:
        cursor.execute(f'SELECT name FROM sqlite_master WHERE type="table" AND name="{table}"')
        if not cursor.fetchone():
            print(f'Creating {table} table...')
            if table == 'user':
                cursor.execute('''
                    CREATE TABLE user (
                        id INTEGER PRIMARY KEY,
                        username VARCHAR(80) UNIQUE NOT NULL,
                        password_hash VARCHAR(128) NOT NULL,
                        role VARCHAR(20) NOT NULL,
                        secret_question VARCHAR(200),
                        secret_answer VARCHAR(200),
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            elif table == 'sale':
                cursor.execute('''
                    CREATE TABLE sale (
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER REFERENCES user(id),
                        total_amount FLOAT NOT NULL,
                        discount_percent FLOAT DEFAULT 0,
                        discount_amount FLOAT DEFAULT 0,
                        final_amount FLOAT NOT NULL,
                        profit FLOAT NOT NULL,
                        receipt_number VARCHAR(20) UNIQUE NOT NULL,
                        cash_received FLOAT,
                        change_amount FLOAT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            elif table == 'sale_item':
                cursor.execute('''
                    CREATE TABLE sale_item (
                        id INTEGER PRIMARY KEY,
                        sale_id INTEGER REFERENCES sale(id),
                        item_id INTEGER REFERENCES item(id),
                        quantity INTEGER NOT NULL,
                        unit_price FLOAT NOT NULL,
                        total_price FLOAT NOT NULL
                    )
                ''')
            elif table == 'branding':
                cursor.execute('''
                    CREATE TABLE branding (
                        id INTEGER PRIMARY KEY,
                        app_name VARCHAR(100) DEFAULT 'POS System',
                        app_subtitle VARCHAR(200) DEFAULT 'Professional Point of Sale',
                        business_name VARCHAR(200),
                        business_address VARCHAR(500),
                        business_phone VARCHAR(50),
                        business_email VARCHAR(100),
                        tax_id VARCHAR(50),
                        primary_color VARCHAR(7) DEFAULT '#6366f1',
                        secondary_color VARCHAR(7) DEFAULT '#8b5cf6',
                        accent_color VARCHAR(7) DEFAULT '#10b981',
                        background_color VARCHAR(7) DEFAULT '#ffffff',
                        text_color VARCHAR(7) DEFAULT '#1f2937',
                        font_family VARCHAR(100) DEFAULT 'Inter',
                        logo_url VARCHAR(500),
                        favicon_url VARCHAR(500),
                        footer_text VARCHAR(500) DEFAULT 'Thank you for your business!',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            elif table == 'activity_log':
                cursor.execute('''
                    CREATE TABLE activity_log (
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER REFERENCES user(id),
                        username VARCHAR(80) NOT NULL,
                        action VARCHAR(100) NOT NULL,
                        action_category VARCHAR(50) NOT NULL,
                        resource_type VARCHAR(50) NOT NULL,
                        resource_id INTEGER,
                        resource_name VARCHAR(200),
                        details TEXT,
                        old_value TEXT,
                        new_value TEXT,
                        ip_address VARCHAR(45),
                        user_agent VARCHAR(500),
                        session_id VARCHAR(100),
                        terminal_id VARCHAR(50),
                        location VARCHAR(100),
                        status VARCHAR(20) DEFAULT 'success',
                        error_message TEXT,
                        severity VARCHAR(20) DEFAULT 'info',
                        compliance_flag BOOLEAN DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        retention_date DATETIME
                    )
                ''')
            conn.commit()

    conn.close()
    print('Root pos.db schema fixed successfully!')

if __name__ == '__main__':
    fix_database_schema()
