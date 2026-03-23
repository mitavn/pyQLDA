from models.user import db
from datetime import datetime


class Quote(db.Model):
    __tablename__ = 'quotes'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)

    # Thông tin báo giá
    title = db.Column(db.String(500), nullable=False)
    quote_number = db.Column(db.String(50))
    status = db.Column(db.String(30), default='draft')  # draft, sent, accepted, rejected
    valid_until = db.Column(db.Date)
    currency = db.Column(db.String(10), default='VND')

    # Liên kết
    contact_id = db.Column(db.Integer, db.ForeignKey('contacts.id'))
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))
    deal_id = db.Column(db.Integer, db.ForeignKey('deals.id'))

    # Tài chính
    subtotal = db.Column(db.Float, default=0)
    tax_rate = db.Column(db.Float, default=10)  # %
    tax_amount = db.Column(db.Float, default=0)
    discount_total = db.Column(db.Float, default=0)
    grand_total = db.Column(db.Float, default=0)

    # Ghi chú
    notes = db.Column(db.Text)
    terms = db.Column(db.Text)

    # Người liên quan
    prepared_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    prepared_for = db.Column(db.String(300))

    # Hệ thống
    sharing = db.Column(db.String(20), default='public')
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    contact = db.relationship('Contact', backref='quotes', foreign_keys=[contact_id])
    company = db.relationship('Company', backref='quotes', foreign_keys=[company_id])
    deal = db.relationship('Deal', backref='quotes', foreign_keys=[deal_id])
    owner = db.relationship('User', foreign_keys=[owner_id])
    preparer = db.relationship('User', foreign_keys=[prepared_by])
    items = db.relationship('QuoteItem', backref='quote', cascade='all, delete-orphan',
                            order_by='QuoteItem.sort_order')

    def recalculate(self):
        """Tính lại tổng tiền từ line items."""
        self.subtotal = sum(item.total for item in self.items)
        self.discount_total = sum(item.discount_amount for item in self.items)
        self.tax_amount = self.subtotal * (self.tax_rate or 0) / 100
        self.grand_total = self.subtotal + self.tax_amount

    @property
    def status_label(self):
        labels = {
            'draft': 'Nháp',
            'sent': 'Đã gửi',
            'accepted': 'Chấp nhận',
            'rejected': 'Từ chối'
        }
        return labels.get(self.status, self.status)

    @property
    def status_color(self):
        colors = {
            'draft': '#8c8c8c',
            'sent': '#1890ff',
            'accepted': '#52c41a',
            'rejected': '#ff4d4f'
        }
        return colors.get(self.status, '#8c8c8c')

    def __repr__(self):
        return f'<Quote {self.title}>'


class QuoteItem(db.Model):
    __tablename__ = 'quote_items'
    id = db.Column(db.Integer, primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey('quotes.id'), nullable=False)

    # Liên kết sản phẩm
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))

    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    unit = db.Column(db.String(50))  # Đơn vị tính (từ Product)
    unit_price = db.Column(db.Float, default=0)
    quantity = db.Column(db.Float, default=1)
    discount = db.Column(db.Float, default=0)  # % giảm giá
    sort_order = db.Column(db.Integer, default=0)

    # Relationship
    product = db.relationship('Product', foreign_keys=[product_id])

    @property
    def discount_amount(self):
        return (self.unit_price or 0) * (self.quantity or 0) * (self.discount or 0) / 100

    @property
    def total(self):
        raw = (self.unit_price or 0) * (self.quantity or 0)
        return raw - self.discount_amount

    def __repr__(self):
        return f'<QuoteItem {self.title}>'
