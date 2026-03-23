"""QuoteService — Data provider for Quote resources."""
from datetime import datetime
from sqlalchemy import or_
from models.user import db
from models.quote import Quote, QuoteItem
from models.contact import Contact
from models.company import Company
from models.deal import Deal
from models.product import Product, StockOrder, StockOrderItem
from services.base_data_provider import BaseDataProvider

QUOTE_STATUSES = ['draft', 'sent', 'accepted', 'rejected']


class QuoteService(BaseDataProvider):

    model = Quote
    module_name = 'quote'

    def build_search_filter(self, query, search):
        return query.filter(Quote.title.ilike(f'%{search}%'))

    # ── Create (with line items) ────────────────────────────────
    def create_with_items(self, tenant_id, form, user_id):
        """Create a quote from form data including line items."""
        quote = Quote(
            tenant_id=tenant_id,
            created_by=user_id,
            owner_id=user_id,
            prepared_by=user_id,
            title=form.get('title', '').strip(),
            quote_number=form.get('quote_number', '').strip(),
            status=form.get('status', 'draft'),
            currency=form.get('currency', 'VND'),
            tax_rate=float(form.get('tax_rate', 10) or 10),
            notes=form.get('notes', '').strip(),
            terms=form.get('terms', '').strip(),
            prepared_for=form.get('prepared_for', '').strip(),
        )

        # Parse valid_until
        valid_str = form.get('valid_until', '').strip()
        if valid_str:
            try:
                quote.valid_until = datetime.strptime(valid_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        # FK links
        for fk in ('contact_id', 'company_id', 'deal_id'):
            val = form.get(fk, '')
            if val:
                setattr(quote, fk, int(val))

        # Line items
        self._parse_line_items(quote, form)

        db.session.add(quote)
        db.session.flush()
        quote.recalculate()
        db.session.commit()
        return quote

    # ── Update (with line items) ────────────────────────────────
    def update_with_items(self, tenant_id, quote_id, form):
        """Update a quote including replacing line items."""
        quote = self.get_one(tenant_id, quote_id)

        quote.title = form.get('title', '').strip()
        quote.quote_number = form.get('quote_number', '').strip()
        quote.status = form.get('status', 'draft')
        quote.currency = form.get('currency', 'VND')
        quote.tax_rate = float(form.get('tax_rate', 10) or 10)
        quote.notes = form.get('notes', '').strip()
        quote.terms = form.get('terms', '').strip()
        quote.prepared_for = form.get('prepared_for', '').strip()

        valid_str = form.get('valid_until', '').strip()
        if valid_str:
            try:
                quote.valid_until = datetime.strptime(valid_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        else:
            quote.valid_until = None

        for fk in ('contact_id', 'company_id', 'deal_id'):
            val = form.get(fk, '')
            setattr(quote, fk, int(val) if val else None)

        # Replace line items
        QuoteItem.query.filter_by(quote_id=quote.id).delete()
        self._parse_line_items(quote, form, existing_quote_id=quote.id)

        db.session.flush()
        quote.recalculate()
        db.session.commit()
        return quote

    # ── Status transition ───────────────────────────────────────
    def update_status(self, tenant_id, quote_id, new_status):
        """Change quote status if valid."""
        if new_status not in QUOTE_STATUSES:
            return None
        quote = self.get_one(tenant_id, quote_id)
        quote.status = new_status
        db.session.commit()
        return quote

    # ── Form options ────────────────────────────────────────────
    def get_form_options(self, tenant_id):
        return {
            'contacts': Contact.query.filter_by(tenant_id=tenant_id).order_by(Contact.first_name).all(),
            'companies': Company.query.filter_by(tenant_id=tenant_id).order_by(Company.name).all(),
            'deals': Deal.query.filter_by(tenant_id=tenant_id).order_by(Deal.name).all(),
            'products': Product.query.filter_by(tenant_id=tenant_id, is_active=True).order_by(Product.name).all(),
        }

    # ── Search products (AJAX) ──────────────────────────────────
    def search_products(self, tenant_id, keyword=''):
        """Search products by name/SKU with stock + planned info."""
        q = Product.query.filter_by(tenant_id=tenant_id, is_active=True)
        if keyword:
            q = q.filter(or_(
                Product.name.ilike(f'%{keyword}%'),
                Product.sku.ilike(f'%{keyword}%'),
                Product.barcode.ilike(f'%{keyword}%')))
        products = q.order_by(Product.name).limit(20).all()

        results = []
        for p in products:
            # Planned import/export from pending stock orders
            planned_import = self._get_planned_qty(tenant_id, p.id, 'planned_import')
            planned_export = self._get_planned_qty(tenant_id, p.id, 'planned_export')
            available = (p.stock_quantity or 0) + planned_import - planned_export

            results.append({
                'id': p.id,
                'name': p.name,
                'sku': p.sku or '',
                'unit': p.unit or 'Cái',
                'sell_price': p.sell_price or 0,
                'cost_price': p.cost_price or 0,
                'stock_quantity': p.stock_quantity or 0,
                'min_stock': p.min_stock or 0,
                'stock_status': p.stock_status,
                'stock_status_label': p.stock_status_label,
                'is_service': p.is_service,
                'category': p.category or '',
                'planned_import': planned_import,
                'planned_export': planned_export,
                'available': round(available, 2),
            })
        return results

    def _get_planned_qty(self, tenant_id, product_id, order_type):
        """Sum planned quantity from pending stock orders."""
        orders = StockOrder.query.filter(
            StockOrder.tenant_id == tenant_id,
            StockOrder.type == order_type,
            StockOrder.status.in_(['draft', 'confirmed'])
        ).all()
        total = 0
        for order in orders:
            for item in order.items:
                if item.product_id == product_id:
                    total += item.quantity or 0
        return round(total, 2)

    # ── Internal ────────────────────────────────────────────────
    def _parse_line_items(self, quote, form, existing_quote_id=None):
        """Parse line item arrays from form."""
        item_titles = form.getlist('item_title[]')
        item_prices = form.getlist('item_price[]')
        item_qtys = form.getlist('item_qty[]')
        item_discounts = form.getlist('item_discount[]')
        item_product_ids = form.getlist('item_product_id[]')
        item_units = form.getlist('item_unit[]')

        for i, title in enumerate(item_titles):
            if not title.strip():
                continue
            product_id = None
            if i < len(item_product_ids) and item_product_ids[i]:
                try:
                    product_id = int(item_product_ids[i])
                except (ValueError, TypeError):
                    pass

            item = QuoteItem(
                title=title.strip(),
                product_id=product_id,
                unit=item_units[i].strip() if i < len(item_units) and item_units[i] else None,
                unit_price=float(item_prices[i]) if i < len(item_prices) and item_prices[i] else 0,
                quantity=float(item_qtys[i]) if i < len(item_qtys) and item_qtys[i] else 1,
                discount=float(item_discounts[i]) if i < len(item_discounts) and item_discounts[i] else 0,
                sort_order=i,
            )
            if existing_quote_id:
                item.quote_id = existing_quote_id
                db.session.add(item)
            else:
                quote.items.append(item)
