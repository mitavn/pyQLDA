from models.user import db
from datetime import datetime


class Deal(db.Model):
    __tablename__ = 'deals'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)

    # Thông tin deal
    name = db.Column(db.String(300), nullable=False)
    value = db.Column(db.Float, default=0)
    currency = db.Column(db.String(10), default='VND')
    stage = db.Column(db.String(100), default='Tiếp cận')
    # Stages: Tiếp cận → Đánh giá → Đề xuất → Thương lượng → Đóng (Thắng/Thua)
    probability = db.Column(db.Integer, default=10)  # %
    expected_close_date = db.Column(db.Date)
    actual_close_date = db.Column(db.Date)
    status = db.Column(db.String(50), default='open')  # open, won, lost

    # Liên kết
    contact_id = db.Column(db.Integer, db.ForeignKey('contacts.id'))
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))

    # Chi tiết
    source = db.Column(db.String(100))
    description = db.Column(db.Text)
    loss_reason = db.Column(db.String(500))
    competitor = db.Column(db.String(300))
    next_step = db.Column(db.String(500))

    # Tài chính
    discount = db.Column(db.Float, default=0)
    tax = db.Column(db.Float, default=0)
    total_amount = db.Column(db.Float, default=0)
    contract_number = db.Column(db.String(100))
    payment_terms = db.Column(db.String(200))

    # Hệ thống
    sharing = db.Column(db.String(20), default='public')  # private, department, public
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    contact = db.relationship('Contact', backref='deals', foreign_keys=[contact_id])
    company = db.relationship('Company', backref='deals', foreign_keys=[company_id])
    owner = db.relationship('User', foreign_keys=[owner_id])

    @property
    def weighted_value(self):
        return (self.value or 0) * (self.probability or 0) / 100

    def __repr__(self):
        return f'<Deal {self.name}>'
