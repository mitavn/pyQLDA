from models.user import db
from datetime import datetime


class Activity(db.Model):
    __tablename__ = 'activities'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)

    # Thông tin hoạt động
    type = db.Column(db.String(50), nullable=False)  # call, meeting, email, task, note
    title = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='planned')  # planned, completed, cancelled
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, urgent

    # Thời gian
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    duration_minutes = db.Column(db.Integer)
    reminder_date = db.Column(db.DateTime)

    # Địa điểm & kết quả
    location = db.Column(db.String(500))
    result = db.Column(db.Text)

    # Liên kết
    contact_id = db.Column(db.Integer, db.ForeignKey('contacts.id'))
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))
    deal_id = db.Column(db.Integer, db.ForeignKey('deals.id'))

    # Hệ thống
    sharing = db.Column(db.String(20), default='public')  # private, department, public
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    contact = db.relationship('Contact', backref='activities', foreign_keys=[contact_id])
    company = db.relationship('Company', backref='activities', foreign_keys=[company_id])
    deal = db.relationship('Deal', backref='activities', foreign_keys=[deal_id])
    owner = db.relationship('User', foreign_keys=[owner_id])

    @property
    def type_icon(self):
        icons = {
            'call': '📞', 'meeting': '🤝', 'email': '✉️',
            'task': '✅', 'note': '📝'
        }
        return icons.get(self.type, '📋')

    def __repr__(self):
        return f'<Activity {self.title}>'
