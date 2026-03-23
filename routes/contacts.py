from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from services.contact_service import ContactService
from services.field_service import get_visible_fields
from services.form_parser import parse_form_data
from services.base_data_provider import ValidationError
from services.log_service import log_action

contacts_bp = Blueprint('contacts', __name__, url_prefix='/contacts')
service = ContactService()


@contacts_bp.route('/')
@login_required
def list_contacts():
    tenant_id = current_user.tenant_id
    search = request.args.get('search', '').strip()
    category = request.args.get('category', '')
    source = request.args.get('source', '')
    page = request.args.get('page', 1, type=int)

    filters = {}
    if category:
        filters['category'] = category
    if source:
        filters['source'] = source

    contacts = service.get_list(tenant_id, filters=filters, search=search, page=page)

    return render_template('contacts/list.html',
                           contacts=contacts,
                           search=search,
                           category=category,
                           source=source)


@contacts_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    tenant_id = current_user.tenant_id
    companies = service.get_companies(tenant_id)
    field_configs = get_visible_fields(tenant_id, 'contact')

    if request.method == 'POST':
        data = parse_form_data(request.form, field_configs)
        try:
            contact = service.create(tenant_id, data, current_user.id)
            log_action('create', 'contacts', contact.id, contact.full_name)
            flash('Đã tạo liên hệ mới thành công!', 'success')
            return redirect(url_for('contacts.detail', id=contact.id))
        except ValidationError as e:
            flash(e.message, 'error')

    return render_template('contacts/form.html',
                           contact=None,
                           companies=companies,
                           field_configs=field_configs,
                           title='Tạo liên hệ mới')


@contacts_bp.route('/<int:id>')
@login_required
def detail(id):
    tenant_id = current_user.tenant_id
    contact = service.get_one(tenant_id, id)
    field_configs = get_visible_fields(tenant_id, 'contact')
    related = service.get_related(tenant_id, id)

    return render_template('contacts/detail.html',
                           contact=contact,
                           field_configs=field_configs,
                           activities=related['activities'],
                           notes=related['notes'],
                           companies=related['companies'])


@contacts_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    tenant_id = current_user.tenant_id
    contact = service.get_one(tenant_id, id)
    companies = service.get_companies(tenant_id)
    field_configs = get_visible_fields(tenant_id, 'contact')

    if request.method == 'POST':
        data = parse_form_data(request.form, field_configs)
        try:
            service.update(tenant_id, id, data)
            log_action('edit', 'contacts', id, contact.full_name)
            flash('Đã cập nhật liên hệ thành công!', 'success')
            return redirect(url_for('contacts.detail', id=id))
        except ValidationError as e:
            flash(e.message, 'error')

    return render_template('contacts/form.html',
                           contact=contact,
                           companies=companies,
                           field_configs=field_configs,
                           title='Chỉnh sửa liên hệ')


@contacts_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    contact = service.get_one(current_user.tenant_id, id)
    log_action('delete', 'contacts', id, contact.full_name)
    service.delete(current_user.tenant_id, id)
    flash('Đã xóa liên hệ.', 'success')
    return redirect(url_for('contacts.list_contacts'))
