from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.user import db, User
from models.department import Department, Position
from services.department_service import (
    get_departments, get_department, create_department, update_department, delete_department,
    get_positions, get_position, create_position, update_position, delete_position,
    assign_user_department, get_department_members
)
from services.permission_service import get_roles

departments_bp = Blueprint('departments', __name__, url_prefix='/departments')


@departments_bp.route('/')
@login_required
def list_departments():
    tenant_id = current_user.tenant_id
    departments = get_departments(tenant_id)
    positions = get_positions(tenant_id)
    users = User.query.filter_by(tenant_id=tenant_id, is_active=True)\
        .order_by(User.full_name).all()
    roles = get_roles(tenant_id)
    return render_template('departments/list.html',
                           departments=departments,
                           positions=positions,
                           users=users,
                           roles=roles)


@departments_bp.route('/create', methods=['POST'])
@login_required
def create_dept():
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    parent_id = request.form.get('parent_id', type=int)
    manager_id = request.form.get('manager_id', type=int)

    if not name:
        flash('Tên phòng ban không được để trống.', 'error')
        return redirect(url_for('departments.list_departments'))

    create_department(current_user.tenant_id, name, description, parent_id, manager_id)
    flash('Đã tạo phòng ban mới.', 'success')
    return redirect(url_for('departments.list_departments'))


@departments_bp.route('/<int:id>/edit', methods=['POST'])
@login_required
def edit_dept(id):
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    parent_id = request.form.get('parent_id', type=int)
    manager_id = request.form.get('manager_id', type=int)

    update_department(current_user.tenant_id, id,
                      name=name, description=description,
                      parent_id=parent_id, manager_id=manager_id)
    flash('Đã cập nhật phòng ban.', 'success')
    return redirect(url_for('departments.list_departments'))


@departments_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_dept(id):
    delete_department(current_user.tenant_id, id)
    flash('Đã xóa phòng ban.', 'success')
    return redirect(url_for('departments.list_departments'))


# Positions
@departments_bp.route('/positions/create', methods=['POST'])
@login_required
def create_pos():
    name = request.form.get('name', '').strip()
    level = request.form.get('level', 1, type=int)
    department_id = request.form.get('department_id', type=int)
    description = request.form.get('description', '').strip()

    if not name:
        flash('Tên chức vụ không được để trống.', 'error')
        return redirect(url_for('departments.list_departments'))

    create_position(current_user.tenant_id, name, level, department_id, description)
    flash('Đã tạo chức vụ mới.', 'success')
    return redirect(url_for('departments.list_departments'))


@departments_bp.route('/positions/<int:id>/edit', methods=['POST'])
@login_required
def edit_pos(id):
    name = request.form.get('name', '').strip()
    level = request.form.get('level', 1, type=int)
    department_id = request.form.get('department_id', type=int)
    description = request.form.get('description', '').strip()

    update_position(current_user.tenant_id, id,
                    name=name, level=level,
                    department_id=department_id, description=description)
    flash('Đã cập nhật chức vụ.', 'success')
    return redirect(url_for('departments.list_departments'))


@departments_bp.route('/positions/<int:id>/delete', methods=['POST'])
@login_required
def delete_pos(id):
    delete_position(current_user.tenant_id, id)
    flash('Đã xóa chức vụ.', 'success')
    return redirect(url_for('departments.list_departments'))


# Assign user
@departments_bp.route('/assign', methods=['POST'])
@login_required
def assign_user():
    user_id = request.form.get('user_id', type=int)
    department_id = request.form.get('department_id', type=int)
    position_id = request.form.get('position_id', type=int)
    role_id = request.form.get('role_id', type=int)

    user = User.query.filter_by(id=user_id, tenant_id=current_user.tenant_id).first()
    if user:
        user.department_id = department_id
        user.position_id = position_id
        if role_id:
            user.role_id = role_id
        db.session.commit()
        flash(f'Đã cập nhật thông tin nhân viên {user.full_name or user.username}.', 'success')
    else:
        flash('Không tìm thấy nhân viên.', 'error')

    return redirect(url_for('departments.list_departments'))
