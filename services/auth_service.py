from models.user import db, User, Tenant
from services.field_service import seed_default_fields
from services.permission_service import seed_default_roles, get_admin_role
from datetime import datetime


def register_tenant(tenant_name, username, email, password, full_name=None):
    """Đăng ký tenant mới + user admin."""
    tenant = Tenant(name=tenant_name)
    db.session.add(tenant)
    db.session.flush()

    # Seed default roles
    admin_role = seed_default_roles(tenant.id)

    user = User(
        tenant_id=tenant.id,
        username=username,
        email=email,
        full_name=full_name or username,
        role='admin',
        role_id=admin_role.id if admin_role else None
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    # Seed default field configs
    seed_default_fields(tenant.id)

    return tenant, user


def authenticate(username, password):
    """Xác thực đăng nhập."""
    user = User.query.filter(
        (User.username == username) | (User.email == username)
    ).first()
    if user and user.check_password(password) and user.is_active:
        user.last_login = datetime.utcnow()
        db.session.commit()
        return user
    return None
