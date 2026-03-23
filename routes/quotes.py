from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from services.quote_service import QuoteService, QUOTE_STATUSES
from models.product import PRODUCT_UNITS
from services.log_service import log_action

quotes_bp = Blueprint('quotes', __name__, url_prefix='/quotes')
service = QuoteService()


@quotes_bp.route('/')
@login_required
def list_quotes():
    tenant_id = current_user.tenant_id
    search = request.args.get('search', '').strip()
    status = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)

    filters = {}
    if status:
        filters['status'] = status

    quotes = service.get_list(tenant_id, filters=filters, search=search, page=page)
    return render_template('quotes/list.html', quotes=quotes, search=search,
                           status=status, statuses=QUOTE_STATUSES)


@quotes_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    tenant_id = current_user.tenant_id
    options = service.get_form_options(tenant_id)

    if request.method == 'POST':
        quote = service.create_with_items(tenant_id, request.form, current_user.id)
        log_action('create', 'quotes', quote.id, quote.title, value=quote.grand_total)
        flash('Đã tạo báo giá mới!', 'success')
        return redirect(url_for('quotes.detail', id=quote.id))

    return render_template('quotes/form.html', quote=None,
                           contacts=options['contacts'],
                           companies=options['companies'],
                           deals=options['deals'],
                           products=options['products'],
                           product_units=PRODUCT_UNITS,
                           title='Tạo báo giá')


@quotes_bp.route('/<int:id>')
@login_required
def detail(id):
    quote = service.get_one(current_user.tenant_id, id)
    return render_template('quotes/detail.html', quote=quote)


@quotes_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    tenant_id = current_user.tenant_id
    options = service.get_form_options(tenant_id)

    if request.method == 'POST':
        quote = service.update_with_items(tenant_id, id, request.form)
        log_action('edit', 'quotes', id, quote.title, value=quote.grand_total)

        # Auto-save via AJAX — return JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or not request.accept_mimetypes.accept_html:
            return jsonify({'status': 'ok', 'message': 'Đã lưu'})

        flash('Đã cập nhật báo giá!', 'success')
        return redirect(url_for('quotes.detail', id=quote.id))

    quote = service.get_one(tenant_id, id)
    return render_template('quotes/form.html', quote=quote,
                           contacts=options['contacts'],
                           companies=options['companies'],
                           deals=options['deals'],
                           products=options['products'],
                           product_units=PRODUCT_UNITS,
                           title='Sửa báo giá')


@quotes_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    quote = service.get_one(current_user.tenant_id, id)
    log_action('delete', 'quotes', id, quote.title)
    service.delete(current_user.tenant_id, id)
    flash('Đã xóa báo giá.', 'success')
    return redirect(url_for('quotes.list_quotes'))


@quotes_bp.route('/<int:id>/status', methods=['POST'])
@login_required
def update_status(id):
    """Change quote status (draft→sent→accepted/rejected)."""
    new_status = request.form.get('status', '')
    result = service.update_status(current_user.tenant_id, id, new_status)
    if result:
        quote, sync_msg = result
        log_action('status', 'quotes', id, quote.title, details=quote.status_label, value=quote.grand_total)
        flash(f'Trạng thái đã chuyển sang: {quote.status_label}', 'success')
        if sync_msg:
            flash(f'🔗 {sync_msg}', 'info')
    return redirect(url_for('quotes.detail', id=id))


@quotes_bp.route('/api/products/search')
@login_required
def search_products():
    """AJAX: search products with stock info for quote form."""
    keyword = request.args.get('q', '').strip()
    results = service.search_products(current_user.tenant_id, keyword)
    return jsonify(results)
