"""Centralized activity log for the entire application.

Every user action (create, edit, delete, status change, etc.)
is recorded here so the dashboard live-feed can show it to the boss.
"""
from models.user import db
from datetime import datetime


class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # What happened
    action = db.Column(db.String(50), nullable=False)      # create, edit, delete, status, stage, import, export …
    module = db.Column(db.String(50), nullable=False)       # deals, contacts, companies, quotes, products …
    entity_id = db.Column(db.Integer)                       # ID of the affected record
    entity_name = db.Column(db.String(300))                 # Human-readable name/title
    details = db.Column(db.String(500))                     # Extra context, e.g. "stage: Thương lượng → Đóng thắng"
    value = db.Column(db.Float, default=0)                  # Monetary value if applicable

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id])

    # Icons by module
    MODULE_ICONS = {
        'deals': '🤝', 'contacts': '👤', 'companies': '🏢',
        'quotes': '📄', 'products': '📦', 'activities': '📋',
        'employees': '👥', 'departments': '🏗️', 'settings': '⚙️',
        'orders': '📦', 'inventory': '📊',
    }
    ACTION_COLORS = {
        'create': '#52c41a', 'edit': '#1890ff', 'delete': '#ff4d4f',
        'status': '#722ed1', 'stage': '#fa8c16', 'import': '#13c2c2',
        'export': '#eb2f96', 'won': '#52c41a', 'lost': '#ff4d4f',
    }

    @property
    def icon(self):
        return self.MODULE_ICONS.get(self.module, '📋')

    @property
    def color(self):
        return self.ACTION_COLORS.get(self.action, '#1890ff')

    def __repr__(self):
        return f'<ActivityLog {self.action} {self.module} {self.entity_name}>'
