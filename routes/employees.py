from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models.user import db, User
from models.department import Department, Position
from services.permission_service import get_roles
from routes.team import log_activity
from datetime import datetime

employees_bp = Blueprint('employees', __name__, url_prefix='/employees')


@employees_bp.route('/')
@login_required
def list_employees():
    tenant_id = current_user.tenant_id
    search = request.args.get('q', '')
    dept_filter = request.args.get('dept', '', type=str)
    status_filter = request.args.get('status', 'active')

    query = User.query.filter_by(tenant_id=tenant_id)

    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)

    if search:
        query = query.filter(
            db.or_(
                User.full_name.ilike(f'%{search}%'),
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
                User.employee_code.ilike(f'%{search}%'),
                User.phone.ilike(f'%{search}%'),
            )
        )

    if dept_filter:
        query = query.filter_by(department_id=int(dept_filter))

    employees = query.order_by(User.full_name).all()
    departments = Department.query.filter_by(tenant_id=tenant_id, is_active=True).all()
    positions = Position.query.filter_by(tenant_id=tenant_id, is_active=True).all()
    roles = get_roles(tenant_id)

    # Stats
    total = User.query.filter_by(tenant_id=tenant_id).count()
    active = User.query.filter_by(tenant_id=tenant_id, is_active=True).count()
    online = sum(1 for e in employees if e.is_online)

    return render_template('employees/list.html',
                           employees=employees, departments=departments,
                           positions=positions, roles=roles,
                           search=search, dept_filter=dept_filter,
                           status_filter=status_filter,
                           total=total, active=active, online=online)


@employees_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_employee():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        full_name = request.form.get('full_name', '').strip()

        if not username or not email or not password:
            flash('Username, email và mật khẩu không được để trống.', 'error')
            return redirect(url_for('employees.create_employee'))

        # Check duplicates
        existing = User.query.filter(
            User.tenant_id == current_user.tenant_id,
            db.or_(User.username == username, User.email == email)
        ).first()
        if existing:
            flash('Username hoặc email đã tồn tại.', 'error')
            return redirect(url_for('employees.create_employee'))

        emp = User(
            tenant_id=current_user.tenant_id,
            username=username,
            email=email,
            full_name=full_name,
            role='user',
        )
        emp.set_password(password)

        # Profile fields
        emp.phone = request.form.get('phone', '').strip() or None
        emp.employee_code = request.form.get('employee_code', '').strip() or None
        emp.gender = request.form.get('gender', '') or None
        emp.address = request.form.get('address', '').strip() or None
        emp.id_card = request.form.get('id_card', '').strip() or None
        emp.bank_account = request.form.get('bank_account', '').strip() or None
        emp.bank_name = request.form.get('bank_name', '').strip() or None
        emp.bio = request.form.get('bio', '').strip() or None

        dob = request.form.get('date_of_birth', '')
        if dob:
            try:
                emp.date_of_birth = datetime.strptime(dob, '%Y-%m-%d').date()
            except ValueError:
                pass
        hire = request.form.get('hire_date', '')
        if hire:
            try:
                emp.hire_date = datetime.strptime(hire, '%Y-%m-%d').date()
            except ValueError:
                pass

        emp.department_id = request.form.get('department_id', type=int)
        emp.position_id = request.form.get('position_id', type=int)
        emp.role_id = request.form.get('role_id', type=int)

        emp.emergency_contact = request.form.get('emergency_contact', '').strip() or None
        emp.emergency_phone = request.form.get('emergency_phone', '').strip() or None

        db.session.add(emp)
        db.session.commit()

        log_activity('create', 'employees', f'Tạo nhân viên {full_name}', 'User', emp.id)
        flash(f'Đã tạo nhân viên {full_name}.', 'success')
        return redirect(url_for('employees.employee_detail', id=emp.id))

    departments = Department.query.filter_by(tenant_id=current_user.tenant_id, is_active=True).all()
    positions = Position.query.filter_by(tenant_id=current_user.tenant_id, is_active=True).all()
    roles = get_roles(current_user.tenant_id)
    return render_template('employees/form.html', employee=None,
                           departments=departments, positions=positions, roles=roles)


@employees_bp.route('/<int:id>')
@login_required
def employee_detail(id):
    emp = User.query.filter_by(id=id, tenant_id=current_user.tenant_id).first_or_404()
    from models.user import UserActivity
    recent_activities = UserActivity.query.filter_by(user_id=emp.id)\
        .order_by(UserActivity.created_at.desc()).limit(20).all()
    return render_template('employees/detail.html', employee=emp,
                           recent_activities=recent_activities)


@employees_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_employee(id):
    emp = User.query.filter_by(id=id, tenant_id=current_user.tenant_id).first_or_404()

    if request.method == 'POST':
        emp.full_name = request.form.get('full_name', '').strip()
        emp.email = request.form.get('email', '').strip()
        emp.phone = request.form.get('phone', '').strip() or None
        emp.employee_code = request.form.get('employee_code', '').strip() or None
        emp.gender = request.form.get('gender', '') or None
        emp.address = request.form.get('address', '').strip() or None
        emp.id_card = request.form.get('id_card', '').strip() or None
        emp.bank_account = request.form.get('bank_account', '').strip() or None
        emp.bank_name = request.form.get('bank_name', '').strip() or None
        emp.bio = request.form.get('bio', '').strip() or None
        emp.emergency_contact = request.form.get('emergency_contact', '').strip() or None
        emp.emergency_phone = request.form.get('emergency_phone', '').strip() or None

        dob = request.form.get('date_of_birth', '')
        emp.date_of_birth = datetime.strptime(dob, '%Y-%m-%d').date() if dob else None
        hire = request.form.get('hire_date', '')
        emp.hire_date = datetime.strptime(hire, '%Y-%m-%d').date() if hire else None

        emp.department_id = request.form.get('department_id', type=int)
        emp.position_id = request.form.get('position_id', type=int)
        emp.role_id = request.form.get('role_id', type=int)

        new_password = request.form.get('new_password', '').strip()
        if new_password:
            emp.set_password(new_password)

        db.session.commit()
        log_activity('update', 'employees', f'Cập nhật NV {emp.full_name}', 'User', emp.id)
        flash('Đã cập nhật thông tin nhân viên.', 'success')
        return redirect(url_for('employees.employee_detail', id=emp.id))

    departments = Department.query.filter_by(tenant_id=current_user.tenant_id, is_active=True).all()
    positions = Position.query.filter_by(tenant_id=current_user.tenant_id, is_active=True).all()
    roles = get_roles(current_user.tenant_id)
    return render_template('employees/form.html', employee=emp,
                           departments=departments, positions=positions, roles=roles)


@employees_bp.route('/<int:id>/toggle-status', methods=['POST'])
@login_required
def toggle_status(id):
    emp = User.query.filter_by(id=id, tenant_id=current_user.tenant_id).first_or_404()
    if emp.id == current_user.id:
        flash('Không thể vô hiệu hóa chính mình.', 'error')
    else:
        emp.is_active = not emp.is_active
        db.session.commit()
        status_text = 'kích hoạt' if emp.is_active else 'vô hiệu hóa'
        log_activity('update', 'employees', f'{status_text} NV {emp.full_name}', 'User', emp.id)
        flash(f'Đã {status_text} nhân viên {emp.full_name or emp.username}.', 'success')
    return redirect(url_for('employees.list_employees'))


@employees_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_employee(id):
    emp = User.query.filter_by(id=id, tenant_id=current_user.tenant_id).first_or_404()
    if emp.id == current_user.id:
        flash('Không thể xóa chính mình.', 'error')
    else:
        log_activity('delete', 'employees', f'Xóa NV {emp.full_name}', 'User', emp.id)
        db.session.delete(emp)
        db.session.commit()
        flash(f'Đã xóa nhân viên {emp.full_name or emp.username}.', 'success')
    return redirect(url_for('employees.list_employees'))


@employees_bp.route('/<int:id>/reset-password', methods=['POST'])
@login_required
def reset_password(id):
    emp = User.query.filter_by(id=id, tenant_id=current_user.tenant_id).first_or_404()
    new_pw = request.form.get('new_password', '').strip()
    if not new_pw or len(new_pw) < 4:
        flash('Mật khẩu phải có ít nhất 4 ký tự.', 'error')
    else:
        emp.set_password(new_pw)
        db.session.commit()
        log_activity('update', 'employees', f'Reset mật khẩu NV {emp.full_name}', 'User', emp.id)
        flash(f'Đã đặt lại mật khẩu cho {emp.full_name or emp.username}.', 'success')
    return redirect(url_for('employees.employee_detail', id=emp.id))


@employees_bp.route('/org-chart')
@login_required
def org_chart():
    """Sơ đồ tổ chức."""
    departments = Department.query.filter_by(
        tenant_id=current_user.tenant_id, is_active=True
    ).order_by(Department.name).all()
    return render_template('employees/org_chart.html', departments=departments)
