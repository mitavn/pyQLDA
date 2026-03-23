from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from services.company_service import CompanyService
from services.field_service import get_visible_fields
from services.form_parser import parse_form_data
from services.base_data_provider import ValidationError
from services.log_service import log_action

companies_bp = Blueprint('companies', __name__, url_prefix='/companies')
service = CompanyService()


@companies_bp.route('/')
@login_required
def list_companies():
    tenant_id = current_user.tenant_id
    search = request.args.get('search', '').strip()
    industry = request.args.get('industry', '')
    page = request.args.get('page', 1, type=int)

    filters = {}
    if industry:
        filters['industry'] = industry

    companies = service.get_list(tenant_id, filters=filters, search=search, page=page)
    return render_template('companies/list.html', companies=companies,
                           search=search, industry=industry)


@companies_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    tenant_id = current_user.tenant_id
    field_configs = get_visible_fields(tenant_id, 'company')

    if request.method == 'POST':
        data = parse_form_data(request.form, field_configs)
        try:
            company = service.create(tenant_id, data, current_user.id)
            log_action('create', 'companies', company.id, company.name)
            flash('Đã tạo công ty mới thành công!', 'success')
            return redirect(url_for('companies.detail', id=company.id))
        except ValidationError as e:
            flash(e.message, 'error')

    return render_template('companies/form.html', company=None,
                           field_configs=field_configs, title='Tạo công ty mới')


@companies_bp.route('/<int:id>')
@login_required
def detail(id):
    tenant_id = current_user.tenant_id
    company = service.get_one(tenant_id, id)
    field_configs = get_visible_fields(tenant_id, 'company')
    related = service.get_related(tenant_id, id)

    return render_template('companies/detail.html',
                           company=company, field_configs=field_configs,
                           contacts=related['contacts'],
                           activities=related['activities'],
                           notes=related['notes'])


@companies_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    tenant_id = current_user.tenant_id
    company = service.get_one(tenant_id, id)
    field_configs = get_visible_fields(tenant_id, 'company')

    if request.method == 'POST':
        data = parse_form_data(request.form, field_configs)
        try:
            service.update(tenant_id, id, data)
            log_action('edit', 'companies', id, company.name)
            flash('Đã cập nhật công ty thành công!', 'success')
            return redirect(url_for('companies.detail', id=id))
        except ValidationError as e:
            flash(e.message, 'error')

    return render_template('companies/form.html', company=company,
                           field_configs=field_configs, title='Chỉnh sửa công ty')


@companies_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    company = service.get_one(current_user.tenant_id, id)
    log_action('delete', 'companies', id, company.name)
    service.delete(current_user.tenant_id, id)
    flash('Đã xóa công ty.', 'success')
    return redirect(url_for('companies.list_companies'))
