from models.user import db
from datetime import datetime


class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    parent_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    parent = db.relationship('Department', remote_side=[id], backref='children')
    manager = db.relationship('User', foreign_keys=[manager_id])
    members = db.relationship('User', backref='department',
                              foreign_keys='User.department_id', lazy=True)

    def __repr__(self):
        return f'<Department {self.name}>'


class Position(db.Model):
    __tablename__ = 'positions'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    level = db.Column(db.Integer, default=1)  # 1=nhân viên, 5=trưởng phòng, 10=giám đốc
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    department = db.relationship('Department', backref='positions')
    users = db.relationship('User', backref='position',
                            foreign_keys='User.position_id', lazy=True)

    def __repr__(self):
        return f'<Position {self.name}>'
