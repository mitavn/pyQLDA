from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from services.activity_service import ActivityService, ACTIVITY_TYPES
from services.field_service import get_visible_fields
from services.form_parser import parse_form_data
from services.log_service import log_action

activities_bp = Blueprint('activities', __name__, url_prefix='/activities')
service = ActivityService()


@activities_bp.route('/')
@login_required
def list_activities():
    tenant_id = current_user.tenant_id
    search = request.args.get('search', '').strip()
    activity_type = request.args.get('type', '')
    status = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)

    filters = {}
    if activity_type:
        filters['type'] = activity_type
    if status:
        filters['status'] = status

    activities = service.get_list(tenant_id, filters=filters, search=search, page=page)
    return render_template('activities/list.html', activities=activities,
                           search=search, activity_type=activity_type,
                           status=status, activity_types=ACTIVITY_TYPES)


@activities_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    tenant_id = current_user.tenant_id
    field_configs = get_visible_fields(tenant_id, 'activity')
    options = service.get_form_options(tenant_id)

    if request.method == 'POST':
        data = parse_form_data(request.form, field_configs)
        act = service.create(tenant_id, data, current_user.id)
        log_action('create', 'activities', act.id if act else None, data.get('subject', ''))
        flash('Đã tạo hoạt động mới thành công!', 'success')
        return redirect(url_for('activities.list_activities'))

    return render_template('activities/form.html', activity=None,
                           contacts=options['contacts'],
                           deals=options['deals'],
                           field_configs=field_configs,
                           activity_types=ACTIVITY_TYPES,
                           title='Tạo hoạt động mới')


@activities_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    tenant_id = current_user.tenant_id
    activity = service.get_one(tenant_id, id)
    field_configs = get_visible_fields(tenant_id, 'activity')
    options = service.get_form_options_all(tenant_id)

    if request.method == 'POST':
        data = parse_form_data(request.form, field_configs)
        service.update(tenant_id, id, data)
        log_action('edit', 'activities', id, data.get('subject', activity.subject if hasattr(activity, 'subject') else ''))
        flash('Đã cập nhật hoạt động thành công!', 'success')
        return redirect(url_for('activities.list_activities'))

    return render_template('activities/form.html', activity=activity,
                           contacts=options['contacts'],
                           deals=options['deals'],
                           field_configs=field_configs,
                           activity_types=ACTIVITY_TYPES,
                           title='Chỉnh sửa hoạt động')


@activities_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    activity = service.get_one(current_user.tenant_id, id)
    log_action('delete', 'activities', id, activity.subject if hasattr(activity, 'subject') else '')
    service.delete(current_user.tenant_id, id)
    flash('Đã xóa hoạt động.', 'success')
    return redirect(url_for('activities.list_activities'))
