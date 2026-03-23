"""Migration: add employee profile fields to users."""
import sqlite3, os

db_path = os.path.join('instance', 'crm.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Add employee fields
c.execute('PRAGMA table_info(users)')
cols = [r[1] for r in c.fetchall()]

new_cols = {
    'employee_code': 'VARCHAR(50)',
    'phone': 'VARCHAR(20)',
    'date_of_birth': 'DATE',
    'gender': 'VARCHAR(10)',
    'address': 'VARCHAR(500)',
    'hire_date': 'DATE',
    'emergency_contact': 'VARCHAR(200)',
    'emergency_phone': 'VARCHAR(20)',
    'id_card': 'VARCHAR(20)',
    'bank_account': 'VARCHAR(50)',
    'bank_name': 'VARCHAR(100)',
    'bio': 'TEXT',
}

for col, col_type in new_cols.items():
    if col not in cols:
        c.execute(f'ALTER TABLE users ADD COLUMN {col} {col_type}')
        print(f'+ Added {col} to users')

conn.commit()
conn.close()
print('Migration complete!')
