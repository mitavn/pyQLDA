from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

db = SQLAlchemy()

ONLINE_THRESHOLD = 60  # seconds


class Tenant(db.Model):
    __tablename__ = 'tenants'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    domain = db.Column(db.String(200), unique=True)
    plan = db.Column(db.String(50), default='free')  # free, pro, enterprise
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    users = db.relationship('User', backref='tenant', lazy=True)

    def __repr__(self):
        return f'<Tenant {self.name}>'


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(200))
    role = db.Column(db.String(50), default='user')  # legacy fallback
    avatar = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # Department & Position
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    position_id = db.Column(db.Integer, db.ForeignKey('positions.id'))

    # Role-based permission
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    # Employee profile
    employee_code = db.Column(db.String(50))  # Mã nhân viên
    phone = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))  # male, female, other
    address = db.Column(db.String(500))
    hire_date = db.Column(db.Date)
    emergency_contact = db.Column(db.String(200))
    emergency_phone = db.Column(db.String(20))
    id_card = db.Column(db.String(20))  # CCCD/CMND
    bank_account = db.Column(db.String(50))
    bank_name = db.Column(db.String(100))
    bio = db.Column(db.Text)

    # Online status (heartbeat)
    last_seen = db.Column(db.DateTime)
    current_page = db.Column(db.String(500))
    current_module = db.Column(db.String(100))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_permission(self, module, action):
        """Kiểm tra quyền qua role_obj."""
        if self.role == 'admin':
            return True
        if self.role_obj:
            return self.role_obj.has_permission(module, action)
        return self.role in ('admin', 'manager')

    def get_scope(self, module):
        """Lấy scope truy cập cho module."""
        if self.role == 'admin':
            return 'all'
        if self.role_obj:
            return self.role_obj.get_scope(module)
        if self.role == 'manager':
            return 'department'
        return 'own'

    @property
    def is_online(self):
        if not self.last_seen:
            return False
        return (datetime.utcnow() - self.last_seen).total_seconds() < ONLINE_THRESHOLD

    @property
    def online_status(self):
        if self.is_online:
            return 'online'
        if self.last_seen and (datetime.utcnow() - self.last_seen).total_seconds() < 300:
            return 'away'
        return 'offline'

    @property
    def online_color(self):
        return {'online': '#52c41a', 'away': '#faad14', 'offline': '#d9d9d9'}.get(self.online_status, '#d9d9d9')

    @property
    def online_label(self):
        return {'online': 'Đang hoạt động', 'away': 'Tạm vắng', 'offline': 'Ngoại tuyến'}.get(self.online_status, 'Ngoại tuyến')

    @property
    def module_label(self):
        labels = {
            'dashboard': 'Tổng quan', 'contacts': 'Liên hệ', 'companies': 'Công ty',
            'deals': 'Deals', 'quotes': 'Báo giá', 'products': 'Sản phẩm',
            'activities': 'Hoạt động', 'settings': 'Cài đặt', 'auth': 'Đăng nhập',
        }
        return labels.get(self.current_module, self.current_module or '')

    @property
    def avatar_url(self):
        if self.avatar:
            return self.avatar
        name = (self.full_name or self.username or 'U')[0].upper()
        return None  # Use initials in template

    @property
    def initials(self):
        if self.full_name:
            parts = self.full_name.split()
            if len(parts) >= 2:
                return (parts[0][0] + parts[-1][0]).upper()
            return parts[0][0].upper()
        return (self.username or 'U')[0].upper()

    def __repr__(self):
        return f'<User {self.username}>'


# ============================================================
# ACTIVITY LOG
# ============================================================
ACTION_TYPES = [
    ('login', 'Đăng nhập'),
    ('logout', 'Đăng xuất'),
    ('page_view', 'Xem trang'),
    ('create', 'Tạo mới'),
    ('update', 'Cập nhật'),
    ('delete', 'Xóa'),
    ('export', 'Xuất dữ liệu'),
    ('import', 'Nhập dữ liệu'),
]


class UserActivity(db.Model):
    """Log hoạt động nhân viên."""
    __tablename__ = 'user_activities'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    action = db.Column(db.String(30), nullable=False)  # login, page_view, create, update, delete...
    module = db.Column(db.String(100))  # dashboard, contacts, deals...
    description = db.Column(db.String(500))
    target_type = db.Column(db.String(100))  # Contact, Deal, Product...
    target_id = db.Column(db.Integer)
    ip_address = db.Column(db.String(50))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id])

    @property
    def action_label(self):
        return dict(ACTION_TYPES).get(self.action, self.action)

    @property
    def action_icon(self):
        icons = {
            'login': 'fa-sign-in-alt', 'logout': 'fa-sign-out-alt',
            'page_view': 'fa-eye', 'create': 'fa-plus-circle',
            'update': 'fa-edit', 'delete': 'fa-trash',
            'export': 'fa-download', 'import': 'fa-upload',
        }
        return icons.get(self.action, 'fa-circle')

    @property
    def action_color(self):
        colors = {
            'login': '#52c41a', 'logout': '#8c8c8c',
            'page_view': '#1890ff', 'create': '#52c41a',
            'update': '#faad14', 'delete': '#ff4d4f',
            'export': '#722ed1', 'import': '#13c2c2',
        }
        return colors.get(self.action, '#8c8c8c')

    def __repr__(self):
        return f'<UserActivity {self.user_id} {self.action}>'


# ============================================================
# CHAT
# ============================================================
class ChatMessage(db.Model):
    """Tin nhắn nhanh giữa nhân viên."""
    __tablename__ = 'chat_messages'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])

    def __repr__(self):
        return f'<Chat {self.sender_id}→{self.receiver_id}>'

