"""Helper to log user actions from anywhere in the app.

Usage:
    from services.log_service import log_action
    log_action('create', 'deals', deal.id, deal.name, value=deal.value)
"""
from flask_login import current_user
from models.user import db
from models.activity_log import ActivityLog


# Vietnamese action labels for the live feed
ACTION_LABELS = {
    'create': 'tạo mới',
    'edit': 'cập nhật',
    'delete': 'xóa',
    'status': 'đổi trạng thái',
    'stage': 'chuyển giai đoạn',
    'won': 'chốt thắng',
    'lost': 'đóng thua',
    'import': 'nhập kho',
    'export': 'xuất kho',
    'count': 'kiểm kho',
    'accept': 'chấp nhận',
    'reject': 'từ chối',
    'send': 'gửi',
}

MODULE_LABELS = {
    'deals': 'deal',
    'contacts': 'liên hệ',
    'companies': 'công ty',
    'quotes': 'báo giá',
    'products': 'sản phẩm',
    'activities': 'hoạt động',
    'employees': 'nhân viên',
    'departments': 'phòng ban',
    'positions': 'chức vụ',
    'settings': 'cài đặt',
    'orders': 'đơn hàng',
    'inventory': 'kho',
    'roles': 'vai trò',
}


def log_action(action, module, entity_id=None, entity_name='', details='', value=0):
    """Record a user action in the activity log.

    Args:
        action: create, edit, delete, status, stage, won, lost, import, export ...
        module: deals, contacts, companies, quotes, products ...
        entity_id: ID of the affected record
        entity_name: Human-readable name
        details: Extra info like "stage: X → Y"
        value: Monetary value if applicable
    """
    try:
        log = ActivityLog(
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            action=action,
            module=module,
            entity_id=entity_id,
            entity_name=str(entity_name)[:300],
            details=str(details)[:500] if details else '',
            value=value or 0,
        )
        db.session.add(log)
        db.session.commit()
    except Exception:
        db.session.rollback()
