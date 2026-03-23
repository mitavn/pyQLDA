from models.user import db
from datetime import datetime


PRODUCT_CATEGORIES = [
    'Phần mềm', 'Phần cứng', 'Dịch vụ', 'Gói giải pháp',
    'Phụ kiện', 'Bảo trì', 'Tư vấn', 'Đào tạo', 'Khác'
]

PRODUCT_UNITS = [
    'Cái', 'Bộ', 'Gói', 'Tháng', 'Năm', 'Giờ', 'Ngày',
    'Lần', 'License', 'User', 'Kg', 'Hộp', 'Chiếc'
]

TRANSACTION_TYPES = [
    ('import', 'Nhập kho'),
    ('export', 'Xuất kho'),
    ('adjust', 'Điều chỉnh'),
    ('return', 'Trả hàng'),
    ('damage', 'Hư hỏng'),
]

ORDER_TYPES = [
    ('planned_import', 'Nhập dự kiến'),
    ('planned_export', 'Xuất dự kiến'),
    ('actual_import', 'Nhập thực tế'),
    ('actual_export', 'Xuất thực tế'),
]

ORDER_STATUSES = [
    ('draft', 'Nháp'),
    ('confirmed', 'Đã xác nhận'),
    ('completed', 'Hoàn thành'),
    ('cancelled', 'Đã hủy'),
]

COUNT_STATUSES = [
    ('draft', 'Đang kiểm'),
    ('completed', 'Hoàn thành'),
    ('cancelled', 'Đã hủy'),
]


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)

    # Thông tin cơ bản
    name = db.Column(db.String(300), nullable=False)
    sku = db.Column(db.String(100))
    barcode = db.Column(db.String(100))
    category = db.Column(db.String(100), default='Khác')
    unit = db.Column(db.String(50), default='Cái')
    description = db.Column(db.Text)
    image_url = db.Column(db.String(500))

    # Giá
    sell_price = db.Column(db.Float, default=0)
    cost_price = db.Column(db.Float, default=0)
    currency = db.Column(db.String(10), default='VND')

    # Kho
    stock_quantity = db.Column(db.Float, default=0)
    min_stock = db.Column(db.Float, default=0)
    max_stock = db.Column(db.Float, default=0)

    # Trạng thái
    is_active = db.Column(db.Boolean, default=True)
    is_service = db.Column(db.Boolean, default=False)

    # Hệ thống
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = db.relationship('User', foreign_keys=[owner_id])
    transactions = db.relationship('StockTransaction', backref='product',
                                   cascade='all, delete-orphan',
                                   order_by='StockTransaction.created_at.desc()')

    @property
    def profit_margin(self):
        if not self.sell_price:
            return 0
        return round((self.sell_price - (self.cost_price or 0)) / self.sell_price * 100, 1)

    @property
    def stock_status(self):
        if self.is_service:
            return 'service'
        if self.stock_quantity <= 0:
            return 'out'
        if self.min_stock and self.stock_quantity <= self.min_stock:
            return 'low'
        return 'in'

    @property
    def stock_status_label(self):
        labels = {'in': 'Còn hàng', 'low': 'Sắp hết', 'out': 'Hết hàng', 'service': 'Dịch vụ'}
        return labels.get(self.stock_status, '')

    @property
    def stock_badge_class(self):
        classes = {'in': 'badge-green', 'low': 'badge-orange', 'out': 'badge-red', 'service': 'badge-blue'}
        return classes.get(self.stock_status, 'badge-default')

    @property
    def stock_value(self):
        if self.is_service:
            return 0
        return (self.cost_price or 0) * (self.stock_quantity or 0)

    def __repr__(self):
        return f'<Product {self.name}>'


class StockTransaction(db.Model):
    """Phiếu nhập/xuất kho đơn lẻ."""
    __tablename__ = 'stock_transactions'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)

    type = db.Column(db.String(30), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit_cost = db.Column(db.Float, default=0)

    stock_before = db.Column(db.Float, default=0)
    stock_after = db.Column(db.Float, default=0)

    reference = db.Column(db.String(200))
    note = db.Column(db.Text)
    partner = db.Column(db.String(300))

    # Liên kết với phiếu kho
    order_id = db.Column(db.Integer, db.ForeignKey('stock_orders.id'))
    count_id = db.Column(db.Integer, db.ForeignKey('inventory_counts.id'))

    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User', foreign_keys=[created_by])

    @property
    def type_label(self):
        labels = dict(TRANSACTION_TYPES)
        return labels.get(self.type, self.type)

    @property
    def type_color(self):
        colors = {
            'import': '#52c41a', 'export': '#1890ff', 'adjust': '#faad14',
            'return': '#722ed1', 'damage': '#ff4d4f',
        }
        return colors.get(self.type, '#8c8c8c')

    @property
    def type_icon(self):
        icons = {
            'import': 'fa-arrow-down', 'export': 'fa-arrow-up',
            'adjust': 'fa-exchange-alt', 'return': 'fa-undo',
            'damage': 'fa-exclamation-triangle',
        }
        return icons.get(self.type, 'fa-circle')

    @property
    def total_value(self):
        return abs(self.quantity or 0) * (self.unit_cost or 0)

    def __repr__(self):
        return f'<StockTransaction {self.type} {self.quantity}>'


# ============================================================
# PHIẾU NHẬP/XUẤT KHO (StockOrder)
# ============================================================
class StockOrder(db.Model):
    """Phiếu nhập/xuất kho chuyên nghiệp (dự kiến + thực tế)."""
    __tablename__ = 'stock_orders'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)

    order_number = db.Column(db.String(50))  # NK-001, XK-001
    type = db.Column(db.String(30), nullable=False)  # planned_import, planned_export, actual_import, actual_export
    status = db.Column(db.String(20), default='draft')  # draft, confirmed, completed, cancelled

    # Đối tác
    partner = db.Column(db.String(300))  # NCC hoặc khách hàng
    partner_contact = db.Column(db.String(300))  # Liên hệ

    # Ngày
    expected_date = db.Column(db.Date)  # Ngày dự kiến
    completed_date = db.Column(db.DateTime)  # Ngày hoàn thành thực tế

    # Giá trị
    total_quantity = db.Column(db.Float, default=0)
    total_value = db.Column(db.Float, default=0)

    # Ghi chú
    note = db.Column(db.Text)

    # Hệ thống
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    confirmed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by])
    confirmer = db.relationship('User', foreign_keys=[confirmed_by])
    items = db.relationship('StockOrderItem', backref='order',
                            cascade='all, delete-orphan', order_by='StockOrderItem.id')
    transactions = db.relationship('StockTransaction', backref='order_ref',
                                   foreign_keys='StockTransaction.order_id')

    def recalculate(self):
        """Tính lại tổng."""
        self.total_quantity = sum(item.quantity or 0 for item in self.items)
        self.total_value = sum(item.total or 0 for item in self.items)

    @property
    def type_label(self):
        labels = dict(ORDER_TYPES)
        return labels.get(self.type, self.type)

    @property
    def type_short(self):
        shorts = {
            'planned_import': 'NK-DK', 'planned_export': 'XK-DK',
            'actual_import': 'NK-TT', 'actual_export': 'XK-TT',
        }
        return shorts.get(self.type, '')

    @property
    def type_color(self):
        colors = {
            'planned_import': '#1890ff', 'planned_export': '#faad14',
            'actual_import': '#52c41a', 'actual_export': '#ff4d4f',
        }
        return colors.get(self.type, '#8c8c8c')

    @property
    def type_icon(self):
        icons = {
            'planned_import': 'fa-clipboard-list', 'planned_export': 'fa-clipboard-list',
            'actual_import': 'fa-arrow-down', 'actual_export': 'fa-arrow-up',
        }
        return icons.get(self.type, 'fa-file')

    @property
    def status_label(self):
        labels = dict(ORDER_STATUSES)
        return labels.get(self.status, self.status)

    @property
    def status_color(self):
        colors = {'draft': '#8c8c8c', 'confirmed': '#1890ff', 'completed': '#52c41a', 'cancelled': '#ff4d4f'}
        return colors.get(self.status, '#8c8c8c')

    @property
    def is_import(self):
        return 'import' in self.type

    @property
    def is_planned(self):
        return 'planned' in self.type

    @property
    def can_confirm(self):
        return self.status == 'draft' and len(self.items) > 0

    @property
    def can_complete(self):
        """Phiếu dự kiến → thực tế, hoặc phiếu thực tế → hoàn thành."""
        return self.status in ('draft', 'confirmed') and len(self.items) > 0

    def __repr__(self):
        return f'<StockOrder {self.order_number} {self.type}>'


class StockOrderItem(db.Model):
    """Dòng sản phẩm trong phiếu nhập/xuất."""
    __tablename__ = 'stock_order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('stock_orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)

    quantity = db.Column(db.Float, default=0)
    unit_cost = db.Column(db.Float, default=0)
    note = db.Column(db.String(500))

    product = db.relationship('Product', foreign_keys=[product_id])

    @property
    def total(self):
        return (self.quantity or 0) * (self.unit_cost or 0)

    def __repr__(self):
        return f'<StockOrderItem {self.product_id} qty={self.quantity}>'


# ============================================================
# KIỂM KHO (InventoryCount)
# ============================================================
class InventoryCount(db.Model):
    """Phiếu kiểm kho hàng loạt."""
    __tablename__ = 'inventory_counts'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)

    count_number = db.Column(db.String(50))  # KK-001
    status = db.Column(db.String(20), default='draft')  # draft, completed, cancelled
    note = db.Column(db.Text)

    # Tổng
    total_products = db.Column(db.Integer, default=0)
    total_difference = db.Column(db.Float, default=0)  # Tổng chênh lệch

    # Hệ thống
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    completed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    creator = db.relationship('User', foreign_keys=[created_by])
    completer = db.relationship('User', foreign_keys=[completed_by])
    items = db.relationship('InventoryCountItem', backref='count',
                            cascade='all, delete-orphan', order_by='InventoryCountItem.id')
    transactions = db.relationship('StockTransaction', backref='count_ref',
                                   foreign_keys='StockTransaction.count_id')

    @property
    def status_label(self):
        labels = dict(COUNT_STATUSES)
        return labels.get(self.status, self.status)

    @property
    def status_color(self):
        colors = {'draft': '#faad14', 'completed': '#52c41a', 'cancelled': '#ff4d4f'}
        return colors.get(self.status, '#8c8c8c')

    def recalculate(self):
        self.total_products = len(self.items)
        self.total_difference = sum(item.difference or 0 for item in self.items)

    def __repr__(self):
        return f'<InventoryCount {self.count_number}>'


class InventoryCountItem(db.Model):
    """Dòng sản phẩm trong phiếu kiểm kho."""
    __tablename__ = 'inventory_count_items'
    id = db.Column(db.Integer, primary_key=True)
    count_id = db.Column(db.Integer, db.ForeignKey('inventory_counts.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)

    system_quantity = db.Column(db.Float, default=0)  # Tồn hệ thống
    actual_quantity = db.Column(db.Float)  # Tồn thực tế (user nhập)
    note = db.Column(db.String(500))

    product = db.relationship('Product', foreign_keys=[product_id])

    @property
    def difference(self):
        if self.actual_quantity is None:
            return 0
        return (self.actual_quantity or 0) - (self.system_quantity or 0)

    @property
    def has_difference(self):
        return self.actual_quantity is not None and self.difference != 0

    def __repr__(self):
        return f'<InventoryCountItem {self.product_id}>'
