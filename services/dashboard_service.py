"""Dashboard Service — Executive command center data."""
from models.user import db, User, ONLINE_THRESHOLD
from models.contact import Contact
from models.company import Company
from models.deal import Deal
from models.activity import Activity
from models.quote import Quote
from sqlalchemy import func, desc
from datetime import datetime, timedelta


# ═══════════════════════════════════════════════════════════
#  KPI STATS
# ═══════════════════════════════════════════════════════════
def get_dashboard_stats(tenant_id):
    """Thống kê tổng quan cho dashboard."""
    total_contacts = Contact.query.filter_by(tenant_id=tenant_id).count()
    total_companies = Company.query.filter_by(tenant_id=tenant_id).count()
    total_deals = Deal.query.filter_by(tenant_id=tenant_id).count()
    total_activities = Activity.query.filter_by(tenant_id=tenant_id).count()

    open_deals = Deal.query.filter_by(tenant_id=tenant_id, status='open').count()
    won_deals = Deal.query.filter_by(tenant_id=tenant_id, status='won').count()
    lost_deals = Deal.query.filter_by(tenant_id=tenant_id, status='lost').count()

    won_deal_list = Deal.query.filter_by(tenant_id=tenant_id, status='won').all()
    total_revenue = sum((d.total_amount or d.value or 0) for d in won_deal_list)

    pipeline_value = db.session.query(func.sum(Deal.value)).filter_by(
        tenant_id=tenant_id, status='open'
    ).scalar() or 0

    closed_deals = won_deals + lost_deals
    win_rate = round(won_deals / closed_deals * 100, 1) if closed_deals > 0 else 0
    avg_deal_value = round(total_revenue / won_deals, 0) if won_deals > 0 else 0

    # Today stats
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_deals = Deal.query.filter(
        Deal.tenant_id == tenant_id,
        Deal.created_at >= today_start
    ).count()
    today_activities = Activity.query.filter(
        Activity.tenant_id == tenant_id,
        Activity.created_at >= today_start
    ).count()
    today_contacts = Contact.query.filter(
        Contact.tenant_id == tenant_id,
        Contact.created_at >= today_start
    ).count()

    return {
        'total_contacts': total_contacts,
        'total_companies': total_companies,
        'total_deals': total_deals,
        'total_activities': total_activities,
        'open_deals': open_deals,
        'won_deals': won_deals,
        'lost_deals': lost_deals,
        'total_revenue': total_revenue,
        'pipeline_value': pipeline_value,
        'win_rate': win_rate,
        'avg_deal_value': avg_deal_value,
        'today_deals': today_deals,
        'today_activities': today_activities,
        'today_contacts': today_contacts,
    }


def get_deals_by_stage(tenant_id):
    stages = ['Tiếp cận', 'Đánh giá', 'Đề xuất', 'Thương lượng', 'Đóng thắng', 'Đóng thua']
    result = {}
    for stage in stages:
        count = Deal.query.filter_by(tenant_id=tenant_id, stage=stage).count()
        value = db.session.query(func.sum(Deal.value)).filter_by(
            tenant_id=tenant_id, stage=stage
        ).scalar() or 0
        result[stage] = {'count': count, 'value': value}
    return result


def get_recent_activities(tenant_id, limit=10):
    return Activity.query.filter_by(tenant_id=tenant_id)\
        .order_by(Activity.created_at.desc())\
        .limit(limit).all()


def get_top_deals(tenant_id, limit=5):
    return Deal.query.filter_by(tenant_id=tenant_id, status='open')\
        .order_by(Deal.value.desc())\
        .limit(limit).all()


def get_monthly_revenue(tenant_id, months=6):
    result = []
    now = datetime.utcnow()
    for i in range(months - 1, -1, -1):
        month_start = (now.replace(day=1) - timedelta(days=30 * i)).replace(day=1)
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1, day=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1, day=1)

        won_deals = Deal.query.filter(
            Deal.tenant_id == tenant_id,
            Deal.status == 'won',
            Deal.actual_close_date >= month_start,
            Deal.actual_close_date < month_end
        ).all()
        revenue = sum((d.total_amount or d.value or 0) for d in won_deals)

        result.append({'month': month_start.strftime('%m/%Y'), 'revenue': revenue})
    return result


# ═══════════════════════════════════════════════════════════
#  EMPLOYEE STATUS & MONITORING
# ═══════════════════════════════════════════════════════════
MODULE_LABELS = {
    'dashboard': '📊 Tổng quan',
    'contacts': '👤 Liên hệ',
    'companies': '🏢 Công ty',
    'deals': '🤝 Deals',
    'quotes': '📄 Báo giá',
    'products': '📦 Sản phẩm',
    'activities': '📋 Hoạt động',
    'employees': '👥 Nhân sự',
    'settings': '⚙️ Cài đặt',
}


def get_employee_status(tenant_id):
    """Get all employees with online/offline status and current activity."""
    users = User.query.filter_by(tenant_id=tenant_id, is_active=True).all()
    threshold = datetime.utcnow() - timedelta(seconds=ONLINE_THRESHOLD)
    result = []
    for u in users:
        is_online = u.last_seen and u.last_seen >= threshold
        module_label = MODULE_LABELS.get(u.current_module, u.current_module or '')
        result.append({
            'id': u.id,
            'full_name': u.full_name or u.username,
            'avatar': u.avatar,
            'username': u.username,
            'is_online': is_online,
            'current_module': module_label,
            'current_page': u.current_page or '',
            'last_seen': u.last_seen.isoformat() if u.last_seen else None,
            'department': u.department.name if u.department_id and u.department else '',
            'position': u.position_obj.name if u.position_id and hasattr(u, 'position_obj') and u.position_obj else '',
        })
    # Online first, then by name
    result.sort(key=lambda x: (not x['is_online'], x['full_name']))
    return result


# ═══════════════════════════════════════════════════════════
#  EMPLOYEE PERFORMANCE
# ═══════════════════════════════════════════════════════════
def get_employee_performance(tenant_id):
    """Rank employees by deals won, activities completed, contacts added."""
    users = User.query.filter_by(tenant_id=tenant_id, is_active=True).all()
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    result = []
    for u in users:
        deals_won = Deal.query.filter(
            Deal.tenant_id == tenant_id,
            Deal.owner_id == u.id,
            Deal.status == 'won'
        ).count()
        deals_lost = Deal.query.filter(
            Deal.tenant_id == tenant_id,
            Deal.owner_id == u.id,
            Deal.status == 'lost'
        ).count()
        revenue = sum(
            (d.total_amount or d.value or 0)
            for d in Deal.query.filter(
                Deal.tenant_id == tenant_id,
                Deal.owner_id == u.id,
                Deal.status == 'won'
            ).all()
        )
        activities_30d = Activity.query.filter(
            Activity.tenant_id == tenant_id,
            Activity.owner_id == u.id,
            Activity.created_at >= thirty_days_ago
        ).count()
        contacts_30d = Contact.query.filter(
            Contact.tenant_id == tenant_id,
            Contact.created_by == u.id,
            Contact.created_at >= thirty_days_ago
        ).count()
        open_deals = Deal.query.filter(
            Deal.tenant_id == tenant_id,
            Deal.owner_id == u.id,
            Deal.status == 'open'
        ).count()

        total_closed = deals_won + deals_lost
        win_rate = round(deals_won / total_closed * 100) if total_closed > 0 else 0

        result.append({
            'id': u.id,
            'full_name': u.full_name or u.username,
            'avatar': u.avatar,
            'deals_won': deals_won,
            'deals_lost': deals_lost,
            'open_deals': open_deals,
            'revenue': revenue,
            'activities_30d': activities_30d,
            'contacts_30d': contacts_30d,
            'win_rate': win_rate,
        })

    result.sort(key=lambda x: (-x['revenue'], -x['deals_won']))
    return result


# ═══════════════════════════════════════════════════════════
#  LIVE FEED  (powered by ActivityLog)
# ═══════════════════════════════════════════════════════════
def get_live_feed(tenant_id, limit=30):
    """Get recent system-wide actions from the centralized activity log."""
    from models.activity_log import ActivityLog
    from services.log_service import ACTION_LABELS, MODULE_LABELS

    logs = ActivityLog.query.filter_by(tenant_id=tenant_id)\
        .order_by(ActivityLog.created_at.desc())\
        .limit(limit).all()

    feed = []
    for log in logs:
        user_name = (log.user.full_name or log.user.username) if log.user else 'Hệ thống'
        action_vn = ACTION_LABELS.get(log.action, log.action)
        module_vn = MODULE_LABELS.get(log.module, log.module)

        # Build readable action text
        if log.entity_name:
            action_text = f'{action_vn} {module_vn} <b>{log.entity_name}</b>'
        else:
            action_text = f'{action_vn} {module_vn}'

        if log.details:
            action_text += f' ({log.details})'

        feed.append({
            'icon': log.icon,
            'user': user_name,
            'action': action_text,
            'value': log.value or 0,
            'time': log.created_at,
            'time_str': _relative_time(log.created_at),
            'color': log.color,
            'type': log.module,
        })

    return feed



# ═══════════════════════════════════════════════════════════
#  ALERTS / ISSUES
# ═══════════════════════════════════════════════════════════
def get_alerts(tenant_id):
    """Detect issues: overdue deals, stale pipeline, low stock."""
    alerts = []
    now = datetime.utcnow()

    # 1. Deals past expected_close_date
    overdue_deals = Deal.query.filter(
        Deal.tenant_id == tenant_id,
        Deal.status == 'open',
        Deal.expected_close_date != None,
        Deal.expected_close_date < now.date()
    ).all()
    for d in overdue_deals:
        days = (now.date() - d.expected_close_date).days
        alerts.append({
            'type': 'overdue',
            'icon': '⏰',
            'severity': 'high' if days > 14 else 'medium',
            'message': f'Deal <b>{d.name}</b> quá hạn {days} ngày',
            'value': d.value or 0,
            'link': f'/deals/{d.id}',
        })

    # 2. High-value deals with no activity in 7+ days
    seven_days_ago = now - timedelta(days=7)
    high_value_deals = Deal.query.filter(
        Deal.tenant_id == tenant_id,
        Deal.status == 'open',
        Deal.value >= 100000  # >100K
    ).all()
    for d in high_value_deals:
        last_activity = Activity.query.filter(
            Activity.tenant_id == tenant_id,
            Activity.deal_id == d.id
        ).order_by(Activity.created_at.desc()).first()
        if not last_activity or last_activity.created_at < seven_days_ago:
            days_inactive = (now - (last_activity.created_at if last_activity else d.created_at)).days
            alerts.append({
                'type': 'stale',
                'icon': '💤',
                'severity': 'medium',
                'message': f'Deal <b>{d.name}</b> ({d.value:,.0f}₫) không có hoạt động {days_inactive} ngày',
                'value': d.value or 0,
                'link': f'/deals/{d.id}',
            })

    # 3. Low stock products
    try:
        from models.product import Product
        low_stock = Product.query.filter(
            Product.tenant_id == tenant_id,
            Product.is_active == True,
            Product.is_service == False,
            Product.stock_quantity <= Product.min_stock,
            Product.min_stock > 0
        ).all()
        for p in low_stock:
            alerts.append({
                'type': 'stock',
                'icon': '📦',
                'severity': 'low',
                'message': f'<b>{p.name}</b> tồn kho thấp: {p.stock_quantity}/{p.min_stock} {p.unit}',
                'value': 0,
                'link': f'/products/{p.id}',
            })
    except Exception:
        pass

    # Sort by severity
    severity_order = {'high': 0, 'medium': 1, 'low': 2}
    alerts.sort(key=lambda x: severity_order.get(x['severity'], 9))
    return alerts


# ═══════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════
def _relative_time(dt_obj):
    """Return human-readable relative time."""
    if not dt_obj:
        return ''
    diff = datetime.utcnow() - dt_obj
    seconds = int(diff.total_seconds())
    if seconds < 60:
        return 'vừa xong'
    elif seconds < 3600:
        return f'{seconds // 60} phút trước'
    elif seconds < 86400:
        return f'{seconds // 3600} giờ trước'
    elif seconds < 604800:
        return f'{seconds // 86400} ngày trước'
    else:
        return dt_obj.strftime('%d/%m/%Y')
