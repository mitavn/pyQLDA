from models.user import db
from datetime import datetime
import json


class FieldConfig(db.Model):
    __tablename__ = 'field_configs'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    module = db.Column(db.String(50), nullable=False)  # contact, company, deal, activity
    field_name = db.Column(db.String(100), nullable=False)
    label = db.Column(db.String(200), nullable=False)
    field_type = db.Column(db.String(50), default='text')  # text, select, date, number, textarea, email, phone
    group_name = db.Column(db.String(200), default='Thông tin chung')
    sort_order = db.Column(db.Integer, default=0)
    is_visible = db.Column(db.Boolean, default=True)
    is_required = db.Column(db.Boolean, default=False)
    options = db.Column(db.Text)  # JSON array for select options
    placeholder = db.Column(db.String(300))

    def get_options(self):
        if self.options:
            try:
                return json.loads(self.options)
            except (json.JSONDecodeError, TypeError):
                return []
        return []

    def __repr__(self):
        return f'<FieldConfig {self.module}.{self.field_name}>'
