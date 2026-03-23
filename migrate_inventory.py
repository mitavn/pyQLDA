"""One-time migration: add StockOrder, InventoryCount tables + FK columns."""
import sqlite3, os

db_path = os.path.join('instance', 'crm.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Check existing columns in stock_transactions
c.execute('PRAGMA table_info(stock_transactions)')
cols = [r[1] for r in c.fetchall()]
print('stock_transactions columns:', cols)

if 'order_id' not in cols:
    c.execute('ALTER TABLE stock_transactions ADD COLUMN order_id INTEGER REFERENCES stock_orders(id)')
    print('+ Added order_id')
if 'count_id' not in cols:
    c.execute('ALTER TABLE stock_transactions ADD COLUMN count_id INTEGER REFERENCES inventory_counts(id)')
    print('+ Added count_id')

# Create new tables
tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print('Existing tables:', tables)

if 'stock_orders' not in tables:
    c.execute('''CREATE TABLE stock_orders (
        id INTEGER PRIMARY KEY,
        tenant_id INTEGER NOT NULL REFERENCES tenants(id),
        order_number VARCHAR(50),
        type VARCHAR(30) NOT NULL,
        status VARCHAR(20) DEFAULT 'draft',
        partner VARCHAR(300),
        partner_contact VARCHAR(300),
        expected_date DATE,
        completed_date DATETIME,
        total_quantity FLOAT DEFAULT 0,
        total_value FLOAT DEFAULT 0,
        note TEXT,
        created_by INTEGER REFERENCES users(id),
        confirmed_by INTEGER REFERENCES users(id),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    print('+ Created stock_orders')

if 'stock_order_items' not in tables:
    c.execute('''CREATE TABLE stock_order_items (
        id INTEGER PRIMARY KEY,
        order_id INTEGER NOT NULL REFERENCES stock_orders(id),
        product_id INTEGER NOT NULL REFERENCES products(id),
        quantity FLOAT DEFAULT 0,
        unit_cost FLOAT DEFAULT 0,
        note VARCHAR(500)
    )''')
    print('+ Created stock_order_items')

if 'inventory_counts' not in tables:
    c.execute('''CREATE TABLE inventory_counts (
        id INTEGER PRIMARY KEY,
        tenant_id INTEGER NOT NULL REFERENCES tenants(id),
        count_number VARCHAR(50),
        status VARCHAR(20) DEFAULT 'draft',
        note TEXT,
        total_products INTEGER DEFAULT 0,
        total_difference FLOAT DEFAULT 0,
        created_by INTEGER REFERENCES users(id),
        completed_by INTEGER REFERENCES users(id),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        completed_at DATETIME
    )''')
    print('+ Created inventory_counts')

if 'inventory_count_items' not in tables:
    c.execute('''CREATE TABLE inventory_count_items (
        id INTEGER PRIMARY KEY,
        count_id INTEGER NOT NULL REFERENCES inventory_counts(id),
        product_id INTEGER NOT NULL REFERENCES products(id),
        system_quantity FLOAT DEFAULT 0,
        actual_quantity FLOAT,
        note VARCHAR(500)
    )''')
    print('+ Created inventory_count_items')

conn.commit()
conn.close()
print('\nMigration complete!')
