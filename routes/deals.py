from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from services.deal_service import DealService, DEAL_STAGES
from services.field_service import get_visible_fields
from services.form_parser import parse_form_data

deals_bp = Blueprint('deals', __name__, url_prefix='/deals')
service = DealService()


@deals_bp.route('/')
@login_required
def list_deals():
    tenant_id = current_user.tenant_id
    search = request.args.get('search', '').strip()
    stage = request.args.get('stage', '')
    status = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)

    filters = {}
    if stage:
        filters['stage'] = stage
    if status:
        filters['status'] = status

    deals = service.get_list(tenant_id, filters=filters, search=search, page=page)
    return render_template('deals/list.html', deals=deals, search=search,
                           stage=stage, status=status, stages=DEAL_STAGES)


@deals_bp.route('/pipeline')
@login_required
def pipeline():
    stages_data = service.get_pipeline(current_user.tenant_id)
    return render_template('deals/pipeline.html', stages_data=stages_data,
                           stages=DEAL_STAGES)


@deals_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    tenant_id = current_user.tenant_id
    field_configs = get_visible_fields(tenant_id, 'deal')
    options = service.get_form_options(tenant_id)

    if request.method == 'POST':
        data = parse_form_data(request.form, field_configs)
        deal = service.create(tenant_id, data, current_user.id)
        flash('Đã tạo deal mới thành công!', 'success')
        return redirect(url_for('deals.detail', id=deal.id))

    return render_template('deals/form.html', deal=None,
                           contacts=options['contacts'],
                           companies=options['companies'],
                           field_configs=field_configs, stages=DEAL_STAGES,
                           title='Tạo deal mới')


@deals_bp.route('/<int:id>')
@login_required
def detail(id):
    tenant_id = current_user.tenant_id
    deal = service.get_one(tenant_id, id)
    field_configs = get_visible_fields(tenant_id, 'deal')
    related = service.get_related(tenant_id, id)

    return render_template('deals/detail.html', deal=deal,
                           field_configs=field_configs,
                           activities=related['activities'],
                           notes=related['notes'],
                           contacts=related['contacts'],
                           companies=related['companies'],
                           stages=DEAL_STAGES)


@deals_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    tenant_id = current_user.tenant_id
    deal = service.get_one(tenant_id, id)
    field_configs = get_visible_fields(tenant_id, 'deal')
    options = service.get_form_options(tenant_id)

    if request.method == 'POST':
        data = parse_form_data(request.form, field_configs)
        service.update(tenant_id, id, data)
        flash('Đã cập nhật deal thành công!', 'success')
        return redirect(url_for('deals.detail', id=id))

    return render_template('deals/form.html', deal=deal,
                           contacts=options['contacts'],
                           companies=options['companies'],
                           field_configs=field_configs, stages=DEAL_STAGES,
                           title='Chỉnh sửa deal')


@deals_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    service.delete(current_user.tenant_id, id)
    flash('Đã xóa deal.', 'success')
    return redirect(url_for('deals.list_deals'))


@deals_bp.route('/<int:id>/move', methods=['POST'])
@login_required
def move_stage(id):
    """AJAX endpoint to move deal to different stage (for pipeline drag-drop)."""
    new_stage = request.json.get('stage')
    success, deal = service.move_stage(current_user.tenant_id, id, new_stage)
    if success:
        return {'success': True, 'stage': deal.stage}
    return {'success': False}, 400
