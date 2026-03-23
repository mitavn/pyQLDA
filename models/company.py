from models.user import db
from datetime import datetime


class Company(db.Model):
    __tablename__ = 'companies'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)

    # Thông tin chung
    name = db.Column(db.String(300), nullable=False)
    short_name = db.Column(db.String(100))
    tax_code = db.Column(db.String(50))
    industry = db.Column(db.String(200))
    company_type = db.Column(db.String(100))  # Công ty TNHH, Cổ phần, ...
    staff_size = db.Column(db.String(50))  # 1-10, 11-50, 51-200, ...
    annual_revenue = db.Column(db.String(100))
    phone = db.Column(db.String(50))
    fax = db.Column(db.String(50))
    email = db.Column(db.String(200))
    website = db.Column(db.String(500))

    # Địa chỉ hóa đơn
    billing_address = db.Column(db.String(500))
    billing_city = db.Column(db.String(100))
    billing_district = db.Column(db.String(100))
    billing_ward = db.Column(db.String(100))
    billing_country = db.Column(db.String(100), default='Việt Nam')

    # Địa chỉ giao hàng
    shipping_address = db.Column(db.String(500))
    shipping_city = db.Column(db.String(100))
    shipping_district = db.Column(db.String(100))
    shipping_ward = db.Column(db.String(100))
    shipping_country = db.Column(db.String(100), default='Việt Nam')

    # Tài chính
    bank_account = db.Column(db.String(50))
    bank_name = db.Column(db.String(200))
    credit_limit = db.Column(db.Float, default=0)
    credit_days = db.Column(db.Integer, default=0)
    debt_amount = db.Column(db.Float, default=0)

    # Bổ sung
    founded_date = db.Column(db.Date)
    description = db.Column(db.Text)
    logo = db.Column(db.String(500))
    tags = db.Column(db.String(500))

    # Hệ thống
    sharing = db.Column(db.String(20), default='public')  # private, department, public
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = db.relationship('User', foreign_keys=[owner_id])

    def __repr__(self):
        return f'<Company {self.name}>'
