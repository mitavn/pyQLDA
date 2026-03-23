"""ProductService — Data provider for Product & inventory resources."""
from datetime import datetime
from models.user import db
from models.product import (Product, StockTransaction, StockOrder, StockOrderItem,
                             InventoryCount, InventoryCountItem,
                             PRODUCT_CATEGORIES, PRODUCT_UNITS, TRANSACTION_TYPES,
                             ORDER_TYPES, ORDER_STATUSES, COUNT_STATUSES)
from services.base_data_provider import BaseDataProvider


class ProductService(BaseDataProvider):

    model = Product
    module_name = 'product'

    def build_search_filter(self, query, search):
        return query.filter(db.or_(
            Product.name.ilike(f'%{search}%'),
            Product.sku.ilike(f'%{search}%'),
        ))

    def default_order(self):
        return [Product.name.asc()]

    def build_filters(self, query, filters):
        category = filters.get('category')
        stock_filter = filters.get('stock')

        if category:
            query = query.filter_by(category=category)
        if stock_filter == 'low':
            query = query.filter(Product.stock_quantity <= Product.min_stock,
                                 Product.is_service == False)
        elif stock_filter == 'out':
            query = query.filter(Product.stock_quantity <= 0,
                                 Product.is_service == False)
        return query

    # ── Summary stats ───────────────────────────────────────────
    def get_list_stats(self, tenant_id):
        """Return summary stats for the product list page."""
        base = Product.query.filter_by(tenant_id=tenant_id)
        total_count = base.count()
        active_count = base.filter_by(is_active=True).count()
        low_stock = base.filter(Product.stock_quantity <= Product.min_stock,
                                Product.min_stock > 0,
                                Product.is_service == False).count()
        total_value = db.session.query(
            db.func.sum(Product.sell_price * Product.stock_quantity)
        ).filter_by(tenant_id=tenant_id, is_service=False).scalar() or 0

        return {
            'total_count': total_count,
            'active_count': active_count,
            'low_stock': low_stock,
            'total_value': total_value,
        }

    # ── Create product ──────────────────────────────────────────
    def create_product(self, tenant_id, form, user_id):
        """Create product from form data, with initial stock transaction."""
        product = Product(
            tenant_id=tenant_id, created_by=user_id, owner_id=user_id,
            name=form.get('name', '').strip(),
            sku=form.get('sku', '').strip(),
            barcode=form.get('barcode', '').strip(),
            category=form.get('category', 'Khác'),
            unit=form.get('unit', 'Cái'),
            description=form.get('description', '').strip(),
            sell_price=float(form.get('sell_price', 0) or 0),
            cost_price=float(form.get('cost_price', 0) or 0),
            currency=form.get('currency', 'VND'),
            stock_quantity=float(form.get('stock_quantity', 0) or 0),
            min_stock=float(form.get('min_stock', 0) or 0),
            max_stock=float(form.get('max_stock', 0) or 0),
            is_active=form.get('is_active') == 'on',
            is_service=form.get('is_service') == 'on',
        )
        db.session.add(product)
        db.session.commit()

        # Initial stock transaction
        if product.stock_quantity > 0 and not product.is_service:
            txn = StockTransaction(
                tenant_id=tenant_id, product_id=product.id,
                type='import', quantity=product.stock_quantity,
                unit_cost=product.cost_price, stock_before=0,
                stock_after=product.stock_quantity, reference='Tồn đầu',
                note='Tồn kho ban đầu khi tạo sản phẩm', created_by=user_id,
            )
            db.session.add(txn)
            db.session.commit()

        return product

    # ── Update product ──────────────────────────────────────────
    def update_product(self, tenant_id, product_id, form):
        """Update product from form data."""
        product = self.get_one(tenant_id, product_id)
        product.name = form.get('name', '').strip()
        product.sku = form.get('sku', '').strip()
        product.barcode = form.get('barcode', '').strip()
        product.category = form.get('category', 'Khác')
        product.unit = form.get('unit', 'Cái')
        product.description = form.get('description', '').strip()
        product.sell_price = float(form.get('sell_price', 0) or 0)
        product.cost_price = float(form.get('cost_price', 0) or 0)
        product.currency = form.get('currency', 'VND')
        product.stock_quantity = float(form.get('stock_quantity', 0) or 0)
        product.min_stock = float(form.get('min_stock', 0) or 0)
        product.max_stock = float(form.get('max_stock', 0) or 0)
        product.is_active = form.get('is_active') == 'on'
        product.is_service = form.get('is_service') == 'on'
        db.session.commit()
        return product

    # ── Stock adjustment ────────────────────────────────────────
    def adjust_stock(self, tenant_id, product_id, form, user_id):
        """Process a stock adjustment transaction."""
        product = self.get_one(tenant_id, product_id)
        txn_type = form.get('type', 'adjust')
        quantity = float(form.get('quantity', 0) or 0)
        unit_cost = float(form.get('unit_cost', 0) or 0) or product.cost_price
        reference = form.get('reference', '').strip()
        note = form.get('note', '').strip()
        partner = form.get('partner', '').strip()

        if txn_type in ('export', 'damage') and quantity > 0:
            quantity = -quantity

        stock_before = product.stock_quantity
        product.stock_quantity += quantity

        txn = StockTransaction(
            tenant_id=tenant_id, product_id=product.id,
            type=txn_type, quantity=quantity, unit_cost=unit_cost,
            stock_before=stock_before, stock_after=product.stock_quantity,
            reference=reference, note=note, partner=partner, created_by=user_id,
        )
        db.session.add(txn)
        db.session.commit()
        return product, txn

    # ── Stock history ───────────────────────────────────────────
    def get_stock_history(self, product_id, page=1, per_page=30):
        return StockTransaction.query.filter_by(product_id=product_id)\
            .order_by(StockTransaction.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)

    def get_all_transactions(self, tenant_id, txn_type=None, page=1, per_page=30):
        query = StockTransaction.query.filter_by(tenant_id=tenant_id)
        if txn_type:
            query = query.filter_by(type=txn_type)
        return query.order_by(StockTransaction.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)

    # ── Stock Orders ────────────────────────────────────────────
    def next_order_number(self, tenant_id, order_type):
        prefix = {'planned_import': 'NK-DK', 'planned_export': 'XK-DK',
                  'actual_import': 'NK', 'actual_export': 'XK'}.get(order_type, 'PH')
        count = StockOrder.query.filter_by(tenant_id=tenant_id).count() + 1
        return f'{prefix}-{count:04d}'

    def get_orders(self, tenant_id, tab=None, page=1, per_page=20):
        query = StockOrder.query.filter_by(tenant_id=tenant_id)
        if tab:
            query = query.filter_by(type=tab)
        return query.order_by(StockOrder.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)

    def get_order_stats(self, tenant_id):
        stats = {}
        for key, label in ORDER_TYPES:
            stats[key] = StockOrder.query.filter_by(tenant_id=tenant_id, type=key)\
                .filter(StockOrder.status != 'cancelled').count()
        return stats

    def get_order(self, tenant_id, order_id):
        return StockOrder.query.filter_by(
            id=order_id, tenant_id=tenant_id
        ).first_or_404()

    def create_order(self, tenant_id, form, user_id):
        """Create a stock order with line items."""
        order_type = form.get('type', 'planned_import')
        order = StockOrder(
            tenant_id=tenant_id,
            order_number=self.next_order_number(tenant_id, order_type),
            type=order_type,
            partner=form.get('partner', '').strip(),
            partner_contact=form.get('partner_contact', '').strip(),
            note=form.get('note', '').strip(),
            created_by=user_id,
        )
        ed = form.get('expected_date')
        if ed:
            try:
                order.expected_date = datetime.strptime(ed, '%Y-%m-%d').date()
            except ValueError:
                pass

        db.session.add(order)
        db.session.flush()

        self._parse_order_items(order, form)
        order.recalculate()
        db.session.commit()
        return order

    def update_order(self, tenant_id, order_id, form):
        """Update an existing draft order."""
        order = self.get_order(tenant_id, order_id)
        order.type = form.get('type', order.type)
        order.partner = form.get('partner', '').strip()
        order.partner_contact = form.get('partner_contact', '').strip()
        order.note = form.get('note', '').strip()

        ed = form.get('expected_date')
        if ed:
            try:
                order.expected_date = datetime.strptime(ed, '%Y-%m-%d').date()
            except ValueError:
                pass

        StockOrderItem.query.filter_by(order_id=order.id).delete()
        self._parse_order_items(order, form)
        order.recalculate()
        db.session.commit()
        return order

    def complete_order(self, tenant_id, order_id, user_id):
        """Complete an order — update stock for each item."""
        order = self.get_order(tenant_id, order_id)

        if order.status not in ('draft', 'confirmed'):
            return None, 'Phiếu đã hoàn thành hoặc đã hủy.'
        if not order.items:
            return None, 'Phiếu chưa có sản phẩm.'

        for item in order.items:
            product = item.product
            stock_before = product.stock_quantity

            if order.is_import:
                product.stock_quantity += item.quantity
                txn_type = 'import'
            else:
                product.stock_quantity -= item.quantity
                txn_type = 'export'

            txn = StockTransaction(
                tenant_id=order.tenant_id, product_id=product.id,
                type=txn_type,
                quantity=item.quantity if order.is_import else -item.quantity,
                unit_cost=item.unit_cost,
                stock_before=stock_before, stock_after=product.stock_quantity,
                reference=order.order_number, note=f'Phiếu {order.type_label}',
                partner=order.partner, order_id=order.id, created_by=user_id,
            )
            db.session.add(txn)

        order.status = 'completed'
        order.completed_date = datetime.utcnow()
        order.confirmed_by = user_id
        db.session.commit()
        return order, None

    def cancel_order(self, tenant_id, order_id):
        order = self.get_order(tenant_id, order_id)
        if order.status == 'completed':
            return None, 'Không thể hủy phiếu đã hoàn thành.'
        order.status = 'cancelled'
        db.session.commit()
        return order, None

    def delete_order(self, tenant_id, order_id):
        order = self.get_order(tenant_id, order_id)
        if order.status == 'completed':
            return False, 'Không thể xóa phiếu đã hoàn thành.'
        db.session.delete(order)
        db.session.commit()
        return True, None

    def get_active_physical_products(self, tenant_id):
        return Product.query.filter_by(
            tenant_id=tenant_id, is_active=True, is_service=False
        ).order_by(Product.name).all()

    # ── Inventory Counts ────────────────────────────────────────
    def next_count_number(self, tenant_id):
        count = InventoryCount.query.filter_by(tenant_id=tenant_id).count() + 1
        return f'KK-{count:04d}'

    def get_counts(self, tenant_id, page=1, per_page=20):
        return InventoryCount.query.filter_by(tenant_id=tenant_id)\
            .order_by(InventoryCount.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)

    def get_count(self, tenant_id, count_id):
        return InventoryCount.query.filter_by(
            id=count_id, tenant_id=tenant_id
        ).first_or_404()

    def create_count(self, tenant_id, form, user_id):
        """Create inventory count with selected or all products."""
        count = InventoryCount(
            tenant_id=tenant_id,
            count_number=self.next_count_number(tenant_id),
            note=form.get('note', '').strip(),
            created_by=user_id,
        )
        db.session.add(count)
        db.session.flush()

        selected = form.getlist('product_ids')
        if selected:
            products = Product.query.filter(
                Product.id.in_([int(x) for x in selected]),
                Product.tenant_id == tenant_id,
            ).all()
        else:
            products = self.get_active_physical_products(tenant_id)

        for p in products:
            item = InventoryCountItem(
                count_id=count.id, product_id=p.id,
                system_quantity=p.stock_quantity,
            )
            db.session.add(item)

        count.total_products = len(products)
        db.session.commit()
        return count

    def update_count_items(self, tenant_id, count_id, form):
        """Save actual quantities for count items."""
        count = self.get_count(tenant_id, count_id)
        for item in count.items:
            val = form.get(f'actual_{item.id}')
            if val is not None and val != '':
                item.actual_quantity = float(val)
            item.note = form.get(f'note_{item.id}', '').strip()
        count.recalculate()
        db.session.commit()
        return count

    def complete_count(self, tenant_id, count_id, user_id):
        """Complete inventory count — adjust stock per actual quantities."""
        count = self.get_count(tenant_id, count_id)
        if count.status != 'draft':
            return None, 'Phiếu đã hoàn thành hoặc hủy.'

        adjusted = 0
        for item in count.items:
            if item.actual_quantity is not None and item.difference != 0:
                product = item.product
                stock_before = product.stock_quantity
                product.stock_quantity = item.actual_quantity

                txn = StockTransaction(
                    tenant_id=count.tenant_id, product_id=product.id,
                    type='adjust', quantity=item.difference,
                    unit_cost=product.cost_price,
                    stock_before=stock_before, stock_after=item.actual_quantity,
                    reference=count.count_number,
                    note=f'Kiểm kho: {item.note or "Điều chỉnh"}',
                    count_id=count.id, created_by=user_id,
                )
                db.session.add(txn)
                adjusted += 1

        count.status = 'completed'
        count.completed_at = datetime.utcnow()
        count.completed_by = user_id
        count.recalculate()
        db.session.commit()
        return count, adjusted

    def cancel_count(self, tenant_id, count_id):
        count = self.get_count(tenant_id, count_id)
        if count.status == 'completed':
            return None, 'Không thể hủy phiếu đã hoàn thành.'
        count.status = 'cancelled'
        db.session.commit()
        return count, None

    # ── API search ──────────────────────────────────────────────
    def api_search(self, tenant_id, q='', limit=20):
        query = Product.query.filter_by(tenant_id=tenant_id, is_active=True)
        if q:
            query = query.filter(db.or_(
                Product.name.ilike(f'%{q}%'),
                Product.sku.ilike(f'%{q}%'),
            ))
        products = query.limit(limit).all()
        return [{
            'id': p.id, 'name': p.name, 'sku': p.sku or '',
            'sell_price': p.sell_price, 'unit': p.unit, 'cost_price': p.cost_price,
            'stock_quantity': p.stock_quantity, 'is_service': p.is_service,
            'category': p.category,
        } for p in products]

    # ── Internal ────────────────────────────────────────────────
    def _parse_order_items(self, order, form):
        idx = 0
        while True:
            pid = form.get(f'items[{idx}][product_id]')
            if pid is None:
                break
            if pid:
                item = StockOrderItem(
                    order_id=order.id,
                    product_id=int(pid),
                    quantity=float(form.get(f'items[{idx}][quantity]', 0) or 0),
                    unit_cost=float(form.get(f'items[{idx}][unit_cost]', 0) or 0),
                    note=form.get(f'items[{idx}][note]', '').strip(),
                )
                db.session.add(item)
            idx += 1
