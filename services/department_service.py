from models.user import db, User
from models.department import Department, Position


def get_departments(tenant_id):
    return Department.query.filter_by(tenant_id=tenant_id, is_active=True)\
        .order_by(Department.name).all()


def get_department(tenant_id, dept_id):
    return Department.query.filter_by(id=dept_id, tenant_id=tenant_id).first()


def create_department(tenant_id, name, description=None, parent_id=None, manager_id=None):
    dept = Department(
        tenant_id=tenant_id,
        name=name,
        description=description,
        parent_id=parent_id,
        manager_id=manager_id
    )
    db.session.add(dept)
    db.session.commit()
    return dept


def update_department(tenant_id, dept_id, **kwargs):
    dept = Department.query.filter_by(id=dept_id, tenant_id=tenant_id).first()
    if dept:
        for key, val in kwargs.items():
            if hasattr(dept, key):
                setattr(dept, key, val)
        db.session.commit()
    return dept


def delete_department(tenant_id, dept_id):
    dept = Department.query.filter_by(id=dept_id, tenant_id=tenant_id).first()
    if dept:
        # Unassign users from department
        User.query.filter_by(department_id=dept_id).update({'department_id': None})
        db.session.delete(dept)
        db.session.commit()
        return True
    return False


# Positions
def get_positions(tenant_id, department_id=None):
    query = Position.query.filter_by(tenant_id=tenant_id, is_active=True)
    if department_id:
        query = query.filter_by(department_id=department_id)
    return query.order_by(Position.level.desc(), Position.name).all()


def get_position(tenant_id, pos_id):
    return Position.query.filter_by(id=pos_id, tenant_id=tenant_id).first()


def create_position(tenant_id, name, level=1, department_id=None, description=None):
    pos = Position(
        tenant_id=tenant_id,
        name=name,
        level=level,
        department_id=department_id,
        description=description
    )
    db.session.add(pos)
    db.session.commit()
    return pos


def update_position(tenant_id, pos_id, **kwargs):
    pos = Position.query.filter_by(id=pos_id, tenant_id=tenant_id).first()
    if pos:
        for key, val in kwargs.items():
            if hasattr(pos, key):
                setattr(pos, key, val)
        db.session.commit()
    return pos


def delete_position(tenant_id, pos_id):
    pos = Position.query.filter_by(id=pos_id, tenant_id=tenant_id).first()
    if pos:
        User.query.filter_by(position_id=pos_id).update({'position_id': None})
        db.session.delete(pos)
        db.session.commit()
        return True
    return False


def assign_user_department(tenant_id, user_id, department_id, position_id=None):
    user = User.query.filter_by(id=user_id, tenant_id=tenant_id).first()
    if user:
        user.department_id = department_id
        if position_id:
            user.position_id = position_id
        db.session.commit()
        return True
    return False


def get_department_members(tenant_id, department_id):
    return User.query.filter_by(
        tenant_id=tenant_id, department_id=department_id
    ).order_by(User.full_name).all()
