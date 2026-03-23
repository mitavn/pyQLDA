from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models.user import db
from services.dashboard_service import (
    get_dashboard_stats, get_deals_by_stage,
    get_recent_activities, get_top_deals, get_monthly_revenue,
    get_employee_status, get_employee_performance,
    get_live_feed, get_alerts
)
from datetime import datetime

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
    employees = get_employee_status(tenant_id)
    performance = get_employee_performance(tenant_id)
    live_feed = get_live_feed(tenant_id, limit=20)
    alerts = get_alerts(tenant_id)

    return render_template('dashboard/index.html',
                           stats=stats,
                           deals_by_stage=deals_by_stage,
                           recent_activities=recent_activities,
                           top_deals=top_deals,
                           monthly_revenue=monthly_revenue,
                           employees=employees,
                           performance=performance,
                           live_feed=live_feed,
                           alerts=alerts)


@dashboard_bp.route('/api/dashboard/live')
@login_required
def live_data():
    """Auto-refresh endpoint — returns JSON for live updates."""
    tenant_id = current_user.tenant_id
    stats = get_dashboard_stats(tenant_id)
    employees = get_employee_status(tenant_id)
    feed = get_live_feed(tenant_id, limit=15)
    alerts = get_alerts(tenant_id)

    # Serialize feed (remove datetime objects)
    for item in feed:
        item.pop('time', None)

    return jsonify({
        'stats': stats,
        'employees': employees,
        'feed': feed,
        'alerts': alerts,
        'server_time': datetime.utcnow().isoformat(),
    })


@dashboard_bp.route('/api/heartbeat', methods=['POST'])
@login_required
def heartbeat():
    """Record user presence — called every 30s from base template."""
    current_user.last_seen = datetime.utcnow()
    page = request.json.get('page', '') if request.is_json else ''
    module = request.json.get('module', '') if request.is_json else ''
    if page:
        current_user.current_page = page[:500]
    if module:
        current_user.current_module = module[:100]
    db.session.commit()
    return jsonify({'ok': True})
