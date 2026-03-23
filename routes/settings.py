from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from models.user import db
from services.field_service import get_field_configs, update_field_order, toggle_field_visibility
from services.permission_service import (
    get_roles, get_role, create_role, update_role_permissions, delete_role,
    MODULES, ACTIONS
)

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')


@settings_bp.route('/fields')
@settings_bp.route('/fields/<module>')
@login_required
def field_config(module='contact'):
    modules = ['contact', 'company', 'deal', 'activity']
    module_labels = {
        'contact': 'Liên hệ',
        'company': 'Công ty',
        'deal': 'Deal',
        'activity': 'Hoạt động',
    }
    if module not in modules:
        module = 'contact'

    fields = get_field_configs(current_user.tenant_id, module)

    # Group by group_name
    grouped = {}
    for f in fields:
        group = f.group_name or 'Khác'
        if group not in grouped:
            grouped[group] = []
        grouped[group].append(f)

    return render_template('settings/field_config.html',
                           fields=fields,
                           grouped=grouped,
                           current_module=module,
                           modules=modules,
                           module_labels=module_labels)


@settings_bp.route('/permissions')
@login_required
def permissions():
    roles = get_roles(current_user.tenant_id)
    module_labels = {
        'contact': 'Liên hệ',
        'company': 'Công ty',
        'deal': 'Deal',
        'activity': 'Hoạt động',
    }
    action_labels = {
        'view': 'Xem',
        'create': 'Tạo',
        'edit': 'Sửa',
        'delete': 'Xóa',
        'export': 'Xuất',
    }
    scope_labels = {
        'own': 'Cá nhân',
        'department': 'Phòng ban',
        'all': 'Tất cả',
    }
    return render_template('settings/permissions.html',
                           roles=roles,
                           modules=MODULES,
                           actions=ACTIONS,
                           module_labels=module_labels,
                           action_labels=action_labels,
                           scope_labels=scope_labels)


@settings_bp.route('/permissions/role/create', methods=['POST'])
@login_required
def create_role_route():
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    if not name:
        flash('Tên vai trò không được để trống.', 'error')
        return redirect(url_for('settings.permissions'))

    create_role(current_user.tenant_id, name, description)
    flash(f'Đã tạo vai trò "{name}".', 'success')
    return redirect(url_for('settings.permissions'))


@settings_bp.route('/permissions/role/<int:role_id>/update', methods=['POST'])
@login_required
def update_permissions_route(role_id):
    permissions_data = {}
    for mod in MODULES:
        permissions_data[mod] = {
            'can_view': request.form.get(f'{mod}_view') == 'on',
            'can_create': request.form.get(f'{mod}_create') == 'on',
            'can_edit': request.form.get(f'{mod}_edit') == 'on',
            'can_delete': request.form.get(f'{mod}_delete') == 'on',
            'can_export': request.form.get(f'{mod}_export') == 'on',
            'scope': request.form.get(f'{mod}_scope', 'own'),
        }
    update_role_permissions(current_user.tenant_id, role_id, permissions_data)
    flash('Đã cập nhật phân quyền.', 'success')
    return redirect(url_for('settings.permissions'))


@settings_bp.route('/permissions/role/<int:role_id>/delete', methods=['POST'])
@login_required
def delete_role_route(role_id):
    if delete_role(current_user.tenant_id, role_id):
        flash('Đã xóa vai trò.', 'success')
    else:
        flash('Không thể xóa vai trò hệ thống.', 'error')
    return redirect(url_for('settings.permissions'))
