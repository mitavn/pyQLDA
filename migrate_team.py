"""Migration: add user online fields, user_activities, chat_messages tables."""
import sqlite3, os

db_path = os.path.join('instance', 'crm.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Add online fields to users
c.execute('PRAGMA table_info(users)')
cols = [r[1] for r in c.fetchall()]
if 'last_seen' not in cols:
    c.execute('ALTER TABLE users ADD COLUMN last_seen DATETIME')
    print('+ Added last_seen to users')
if 'current_page' not in cols:
    c.execute('ALTER TABLE users ADD COLUMN current_page VARCHAR(500)')
    print('+ Added current_page to users')
if 'current_module' not in cols:
    c.execute('ALTER TABLE users ADD COLUMN current_module VARCHAR(100)')
    print('+ Added current_module to users')

# Create user_activities
tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]

if 'user_activities' not in tables:
    c.execute('''CREATE TABLE user_activities (
        id INTEGER PRIMARY KEY,
        tenant_id INTEGER NOT NULL REFERENCES tenants(id),
        user_id INTEGER NOT NULL REFERENCES users(id),
        action VARCHAR(30) NOT NULL,
        module VARCHAR(100),
        description VARCHAR(500),
        target_type VARCHAR(100),
        target_id INTEGER,
        ip_address VARCHAR(50),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    print('+ Created user_activities')

if 'chat_messages' not in tables:
    c.execute('''CREATE TABLE chat_messages (
        id INTEGER PRIMARY KEY,
        tenant_id INTEGER NOT NULL REFERENCES tenants(id),
        sender_id INTEGER NOT NULL REFERENCES users(id),
        receiver_id INTEGER NOT NULL REFERENCES users(id),
        message TEXT NOT NULL,
        is_read BOOLEAN DEFAULT 0,
        read_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    print('+ Created chat_messages')

conn.commit()
conn.close()
print('Migration complete!')
