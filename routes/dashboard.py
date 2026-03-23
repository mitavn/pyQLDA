from flask import Blueprint, render_template
from flask_login import login_required, current_user
from services.dashboard_service import (
    get_dashboard_stats, get_deals_by_stage,
    get_recent_activities, get_top_deals, get_monthly_revenue
)

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    tenant_id = current_user.tenant_id
    stats = get_dashboard_stats(tenant_id)
    deals_by_stage = get_deals_by_stage(tenant_id)
    recent_activities = get_recent_activities(tenant_id, limit=8)
    top_deals = get_top_deals(tenant_id, limit=5)
    monthly_revenue = get_monthly_revenue(tenant_id, months=6)

    return render_template('dashboard/index.html',
                           stats=stats,
                           deals_by_stage=deals_by_stage,
                           recent_activities=recent_activities,
                           top_deals=top_deals,
                           monthly_revenue=monthly_revenue)
