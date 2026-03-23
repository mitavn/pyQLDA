from models.user import db
from datetime import datetime


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_system = db.Column(db.Boolean, default=False)  # True = không xóa được
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    permissions = db.relationship('Permission', backref='role', lazy=True,
                                  cascade='all, delete-orphan')
    users = db.relationship('User', backref='role_obj',
                            foreign_keys='User.role_id', lazy=True)

    def __repr__(self):
        return f'<Role {self.name}>'

    def has_permission(self, module, action):
        """Kiểm tra role có quyền action trên module không."""
        for p in self.permissions:
            if p.module == module:
                return getattr(p, f'can_{action}', False)
        return False

    def get_scope(self, module):
        """Lấy scope truy cập cho module."""
        for p in self.permissions:
            if p.module == module:
                return p.scope
        return 'own'


class Permission(db.Model):
    __tablename__ = 'permissions'
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    module = db.Column(db.String(50), nullable=False)  # contact, company, deal, activity
    can_view = db.Column(db.Boolean, default=True)
    can_create = db.Column(db.Boolean, default=True)
    can_edit = db.Column(db.Boolean, default=True)
    can_delete = db.Column(db.Boolean, default=False)
    can_export = db.Column(db.Boolean, default=False)
    scope = db.Column(db.String(20), default='own')  # own, department, all

    def __repr__(self):
        return f'<Permission {self.module} for Role#{self.role_id}>'
