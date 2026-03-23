from models.user import db
from models.contact import Contact
from models.company import Company
from models.deal import Deal
from models.activity import Activity
from sqlalchemy import func
from datetime import datetime, timedelta


def get_dashboard_stats(tenant_id):
    """Lấy thống kê tổng quan cho dashboard."""
    total_contacts = Contact.query.filter_by(tenant_id=tenant_id).count()
    total_companies = Company.query.filter_by(tenant_id=tenant_id).count()
    total_deals = Deal.query.filter_by(tenant_id=tenant_id).count()
    total_activities = Activity.query.filter_by(tenant_id=tenant_id).count()

    # Deal stats
    open_deals = Deal.query.filter_by(tenant_id=tenant_id, status='open').count()
    won_deals = Deal.query.filter_by(tenant_id=tenant_id, status='won').count()
    lost_deals = Deal.query.filter_by(tenant_id=tenant_id, status='lost').count()

    # Revenue: use total_amount if set, fallback to value
    # total_amount is set when deal is won (from quote or stage move)
    won_deal_list = Deal.query.filter_by(tenant_id=tenant_id, status='won').all()
    total_revenue = sum((d.total_amount or d.value or 0) for d in won_deal_list)

    pipeline_value = db.session.query(func.sum(Deal.value)).filter_by(
        tenant_id=tenant_id, status='open'
    ).scalar() or 0

    # Win rate
    closed_deals = won_deals + lost_deals
    win_rate = round(won_deals / closed_deals * 100, 1) if closed_deals > 0 else 0

    # Average deal value (won deals)
    avg_deal_value = round(total_revenue / won_deals, 0) if won_deals > 0 else 0

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
    }


def get_deals_by_stage(tenant_id):
    """Thống kê deal theo giai đoạn."""
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
    """Lấy hoạt động gần đây."""
    return Activity.query.filter_by(tenant_id=tenant_id)\
        .order_by(Activity.created_at.desc())\
        .limit(limit).all()


def get_top_deals(tenant_id, limit=5):
    """Lấy top deals giá trị cao nhất."""
    return Deal.query.filter_by(tenant_id=tenant_id, status='open')\
        .order_by(Deal.value.desc())\
        .limit(limit).all()


def get_monthly_revenue(tenant_id, months=6):
    """Doanh thu theo tháng (6 tháng gần nhất).
    Uses total_amount (set on won) with fallback to value."""
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

        result.append({
            'month': month_start.strftime('%m/%Y'),
            'revenue': revenue
        })
    return result
