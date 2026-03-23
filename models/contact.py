from models.user import db
from datetime import datetime


class Contact(db.Model):
    __tablename__ = 'contacts'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)

    # Thông tin chung
    customer_code = db.Column(db.String(50))
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(200))
    phone = db.Column(db.String(50))
    mobile = db.Column(db.String(50))
    position = db.Column(db.String(200))
    department = db.Column(db.String(200))
    gender = db.Column(db.String(20))  # Nam, Nữ, Khác
    date_of_birth = db.Column(db.Date)
    customer_type = db.Column(db.String(50))  # Cá nhân, Doanh nghiệp
    category = db.Column(db.String(100))  # VIP, Thường, Tiềm năng
    source = db.Column(db.String(100))  # Website, Giới thiệu, Quảng cáo...

    # Liên kết công ty
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))

    # Địa chỉ
    address = db.Column(db.String(500))
    city = db.Column(db.String(100))
    district = db.Column(db.String(100))
    ward = db.Column(db.String(100))
    country = db.Column(db.String(100), default='Việt Nam')
    zip_code = db.Column(db.String(20))

    # Tài chính / Ngân hàng
    tax_code = db.Column(db.String(50))
    bank_account = db.Column(db.String(50))
    bank_name = db.Column(db.String(200))

    # Mạng xã hội
    website = db.Column(db.String(500))
    facebook = db.Column(db.String(500))
    zalo = db.Column(db.String(100))
    linkedin = db.Column(db.String(500))

    # Bổ sung
    description = db.Column(db.Text)
    tags = db.Column(db.String(500))
    avatar = db.Column(db.String(500))

    # Hệ thống
    sharing = db.Column(db.String(20), default='public')  # private, department, public
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = db.relationship('Company', backref='contacts', foreign_keys=[company_id])
    owner = db.relationship('User', foreign_keys=[owner_id])

    @property
    def full_name(self):
        parts = [self.last_name or '', self.first_name or '']
        return ' '.join(p for p in parts if p)

    def __repr__(self):
        return f'<Contact {self.full_name}>'
