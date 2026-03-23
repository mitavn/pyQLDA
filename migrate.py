"""Migration script to add new columns to existing tables."""
from app import create_app
from models.user import db

app = create_app()
with app.app_context():
    conn = db.engine.raw_connection()
    cursor = conn.cursor()

    # Add missing columns to users table
    for col, coldef in [
        ('department_id', 'INTEGER REFERENCES departments(id)'),
        ('position_id', 'INTEGER REFERENCES positions(id)'),
        ('role_id', 'INTEGER REFERENCES roles(id)'),
    ]:
        try:
            cursor.execute(f'ALTER TABLE users ADD COLUMN {col} {coldef}')
            print(f'+ users.{col}')
        except Exception as e:
            print(f'  users.{col}: already exists or {e}')

    # Add sharing column to entity tables
    for tbl in ['contacts', 'companies', 'deals', 'activities']:
        try:
            cursor.execute(f"ALTER TABLE {tbl} ADD COLUMN sharing VARCHAR(20) DEFAULT 'public'")
            print(f'+ {tbl}.sharing')
        except Exception as e:
            print(f'  {tbl}.sharing: already exists or {e}')

    conn.commit()
    conn.close()

    # Seed default roles for existing tenants
    from models.user import Tenant, User
    from services.permission_service import seed_default_roles, get_admin_role

    tenants = Tenant.query.all()
    for tenant in tenants:
        admin_role = seed_default_roles(tenant.id)
        if admin_role:
            # Assign admin role to admin users
            admins = User.query.filter_by(tenant_id=tenant.id, role='admin').all()
            for u in admins:
                if not u.role_id:
                    u.role_id = admin_role.id
            db.session.commit()
            print(f'+ Seeded roles for tenant: {tenant.name}')

    print('Migration complete!')
