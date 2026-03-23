from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user
from models.user import db, User
from models.role import Role, Permission
from models.department import Department


# Module danh sách
MODULES = ['contact', 'company', 'deal', 'activity']
ACTIONS = ['view', 'create', 'edit', 'delete', 'export']
SCOPES = ['own', 'department', 'all']

# Default roles khi tạo tenant
DEFAULT_ROLES = [
    {
        'name': 'Admin',
        'description': 'Quản trị viên - toàn quyền truy cập',
        'is_system': True,
        'permissions': {mod: {'can_view': True, 'can_create': True, 'can_edit': True,
                              'can_delete': True, 'can_export': True, 'scope': 'all'}
                        for mod in MODULES}
    },
    {
        'name': 'Quản lý',
        'description': 'Quản lý phòng ban - xem dữ liệu phòng ban',
        'is_system': True,
        'permissions': {mod: {'can_view': True, 'can_create': True, 'can_edit': True,
                              'can_delete': False, 'can_export': True, 'scope': 'department'}
                        for mod in MODULES}
    },
    {
        'name': 'Nhân viên',
        'description': 'Nhân viên - chỉ xem dữ liệu cá nhân',
        'is_system': True,
        'permissions': {mod: {'can_view': True, 'can_create': True, 'can_edit': True,
                              'can_delete': False, 'can_export': False, 'scope': 'own'}
                        for mod in MODULES}
    },
]


def seed_default_roles(tenant_id):
    """Tạo roles mặc định cho tenant mới."""
    admin_role = None
    for role_data in DEFAULT_ROLES:
        existing = Role.query.filter_by(tenant_id=tenant_id, name=role_data['name']).first()
        if existing:
            if role_data['name'] == 'Admin':
                admin_role = existing
            continue

        role = Role(
            tenant_id=tenant_id,
            name=role_data['name'],
            description=role_data['description'],
            is_system=role_data['is_system']
        )
        db.session.add(role)
        db.session.flush()

        # Tạo permissions
        for mod, perms in role_data['permissions'].items():
            perm = Permission(
                role_id=role.id,
                module=mod,
                can_view=perms['can_view'],
                can_create=perms['can_create'],
                can_edit=perms['can_edit'],
                can_delete=perms['can_delete'],
                can_export=perms['can_export'],
                scope=perms['scope']
            )
            db.session.add(perm)

        if role_data['name'] == 'Admin':
            admin_role = role

    db.session.commit()
    return admin_role


def get_admin_role(tenant_id):
    """Lấy role Admin."""
    return Role.query.filter_by(tenant_id=tenant_id, name='Admin').first()


def get_roles(tenant_id):
    """Lấy tất cả roles của tenant."""
    return Role.query.filter_by(tenant_id=tenant_id)\
        .order_by(Role.is_system.desc(), Role.name).all()


def get_role(tenant_id, role_id):
    return Role.query.filter_by(id=role_id, tenant_id=tenant_id).first()


def create_role(tenant_id, name, description=None):
    role = Role(tenant_id=tenant_id, name=name, description=description)
    db.session.add(role)
    db.session.flush()
    # Tạo default permissions (tất cả off)
    for mod in MODULES:
        perm = Permission(
            role_id=role.id, module=mod,
            can_view=True, can_create=False, can_edit=False,
            can_delete=False, can_export=False, scope='own'
        )
        db.session.add(perm)
    db.session.commit()
    return role


def update_role_permissions(tenant_id, role_id, permissions_data):
    """Cập nhật permissions cho role.
    permissions_data = {module: {can_view, can_create, can_edit, can_delete, can_export, scope}}
    """
    role = Role.query.filter_by(id=role_id, tenant_id=tenant_id).first()
    if not role:
        return False

    for mod, perms in permissions_data.items():
        perm = Permission.query.filter_by(role_id=role.id, module=mod).first()
        if not perm:
            perm = Permission(role_id=role.id, module=mod)
            db.session.add(perm)
        perm.can_view = perms.get('can_view', False)
        perm.can_create = perms.get('can_create', False)
        perm.can_edit = perms.get('can_edit', False)
        perm.can_delete = perms.get('can_delete', False)
        perm.can_export = perms.get('can_export', False)
        perm.scope = perms.get('scope', 'own')

    db.session.commit()
    return True


def delete_role(tenant_id, role_id):
    role = Role.query.filter_by(id=role_id, tenant_id=tenant_id).first()
    if not role or role.is_system:
        return False
    # Unassign users
    User.query.filter_by(role_id=role_id).update({'role_id': None})
    db.session.delete(role)
    db.session.commit()
    return True


def check_permission(user, module, action):
    """Kiểm tra user có quyền thực hiện action trên module không."""
    if user.role == 'admin':
        return True
    return user.has_permission(module, action)


def get_accessible_query(user, model, base_query):
    """Filter query dựa vào scope + sharing.

    Logic:
    1. Admin → xem tất cả trong tenant
    2. Scope 'all' → xem tất cả sharing='public' + tất cả
    3. Scope 'department' → xem records công khai + records của cùng phòng ban
    4. Scope 'own' → chỉ records mình sở hữu + records sharing='public'
    5. Sharing override: private → chỉ owner, department → owner + cùng dept
    """
    if user.role == 'admin':
        return base_query

    module_map = {
        'Contact': 'contact', 'Company': 'company',
        'Deal': 'deal', 'Activity': 'activity'
    }
    module_name = module_map.get(model.__name__, 'contact')
    scope = user.get_scope(module_name)

    if scope == 'all':
        return base_query

    if scope == 'department' and user.department_id:
        # Lấy danh sách user cùng phòng ban
        dept_user_ids = [u.id for u in
                         User.query.filter_by(
                             tenant_id=user.tenant_id,
                             department_id=user.department_id
                         ).all()]

        return base_query.filter(
            db.or_(
                model.sharing == 'public',
                model.owner_id == user.id,
                db.and_(
                    model.sharing == 'department',
                    model.owner_id.in_(dept_user_ids)
                )
            )
        )
    else:
        # Scope = 'own'
        return base_query.filter(
            db.or_(
                model.sharing == 'public',
                model.owner_id == user.id
            )
        )


def require_permission(module, action):
    """Decorator kiểm tra quyền trước khi vào route."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not check_permission(current_user, module, action):
                flash('Bạn không có quyền thực hiện thao tác này.', 'error')
                return redirect(url_for('dashboard.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
