from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models.user import db, User, UserActivity, ChatMessage, ACTION_TYPES
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_

team_bp = Blueprint('team', __name__, url_prefix='/team')


# ============================================================
# HEARTBEAT — JS pings every 30s
# ============================================================
@team_bp.route('/api/heartbeat', methods=['POST'])
@login_required
def heartbeat():
    """Cập nhật trạng thái online + trang hiện tại."""
    current_user.last_seen = datetime.utcnow()
    current_user.current_page = request.json.get('page', '') if request.is_json else request.form.get('page', '')
    current_user.current_module = request.json.get('module', '') if request.is_json else request.form.get('module', '')
    db.session.commit()
    
    # Return unread message count
    unread = ChatMessage.query.filter_by(
        receiver_id=current_user.id, is_read=False
    ).count()
    
    return jsonify({'status': 'ok', 'unread': unread})


# ============================================================
# ONLINE USERS
# ============================================================
@team_bp.route('/api/online')
@login_required
def online_users():
    """Danh sách nhân viên cùng tenant với trạng thái online."""
    users = User.query.filter_by(
        tenant_id=current_user.tenant_id, is_active=True
    ).order_by(User.last_seen.desc().nullslast()).all()

    return jsonify([{
        'id': u.id,
        'full_name': u.full_name or u.username,
        'initials': u.initials,
        'avatar': u.avatar,
        'status': u.online_status,
        'color': u.online_color,
        'label': u.online_label,
        'module': u.module_label,
        'current_page': u.current_page or '',
        'last_seen': u.last_seen.isoformat() if u.last_seen else None,
        'is_me': u.id == current_user.id,
    } for u in users])


# ============================================================
# ACTIVITY LOG
# ============================================================
@team_bp.route('/activity-log')
@login_required
def activity_log():
    """Trang log hoạt động nhân viên."""
    user_id = request.args.get('user', '', type=str)
    action = request.args.get('action', '')
    date_from = request.args.get('from', '')
    date_to = request.args.get('to', '')
    page = request.args.get('page', 1, type=int)

    query = UserActivity.query.filter_by(tenant_id=current_user.tenant_id)

    if user_id:
        query = query.filter_by(user_id=int(user_id))
    if action:
        query = query.filter_by(action=action)
    if date_from:
        try:
            query = query.filter(UserActivity.created_at >= datetime.strptime(date_from, '%Y-%m-%d'))
        except ValueError:
            pass
    if date_to:
        try:
            query = query.filter(UserActivity.created_at <= datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1))
        except ValueError:
            pass

    activities = query.order_by(UserActivity.created_at.desc())\
        .paginate(page=page, per_page=50, error_out=False)

    users = User.query.filter_by(tenant_id=current_user.tenant_id, is_active=True).all()

    return render_template('team/activity_log.html', activities=activities,
                           users=users, action_types=ACTION_TYPES,
                           filter_user=user_id, filter_action=action,
                           filter_from=date_from, filter_to=date_to)


@team_bp.route('/statistics')
@login_required
def statistics():
    """Thống kê hoạt động nhân viên."""
    tenant_id = current_user.tenant_id
    days = request.args.get('days', 7, type=int)
    since = datetime.utcnow() - timedelta(days=days)

    users = User.query.filter_by(tenant_id=tenant_id, is_active=True).all()

    # Stats per user
    user_stats = []
    for u in users:
        total_actions = UserActivity.query.filter(
            UserActivity.user_id == u.id,
            UserActivity.created_at >= since
        ).count()

        logins = UserActivity.query.filter(
            UserActivity.user_id == u.id,
            UserActivity.action == 'login',
            UserActivity.created_at >= since
        ).count()

        creates = UserActivity.query.filter(
            UserActivity.user_id == u.id,
            UserActivity.action == 'create',
            UserActivity.created_at >= since
        ).count()

        updates = UserActivity.query.filter(
            UserActivity.user_id == u.id,
            UserActivity.action == 'update',
            UserActivity.created_at >= since
        ).count()

        # Active hours (distinct hours)
        active_hours = db.session.query(
            func.count(func.distinct(func.strftime('%Y-%m-%d %H', UserActivity.created_at)))
        ).filter(
            UserActivity.user_id == u.id,
            UserActivity.created_at >= since
        ).scalar() or 0

        user_stats.append({
            'user': u,
            'total_actions': total_actions,
            'logins': logins,
            'creates': creates,
            'updates': updates,
            'active_hours': active_hours,
            'avg_daily': round(total_actions / max(days, 1), 1),
        })

    # Sort by total actions descending
    user_stats.sort(key=lambda x: x['total_actions'], reverse=True)

    # Overall stats
    total_activities = UserActivity.query.filter(
        UserActivity.tenant_id == tenant_id,
        UserActivity.created_at >= since
    ).count()

    online_count = sum(1 for u in users if u.is_online)

    return render_template('team/statistics.html', user_stats=user_stats,
                           days=days, online_count=online_count,
                           total_activities=total_activities,
                           total_users=len(users))


# ============================================================
# CHAT API
# ============================================================
@team_bp.route('/api/chat/contacts')
@login_required
def chat_contacts():
    """Danh sách nhân viên để chat, với tin nhắn cuối + unread count."""
    users = User.query.filter(
        User.tenant_id == current_user.tenant_id,
        User.is_active == True,
        User.id != current_user.id
    ).order_by(User.last_seen.desc().nullslast()).all()

    contacts = []
    for u in users:
        # Last message
        last_msg = ChatMessage.query.filter(
            or_(
                and_(ChatMessage.sender_id == current_user.id, ChatMessage.receiver_id == u.id),
                and_(ChatMessage.sender_id == u.id, ChatMessage.receiver_id == current_user.id),
            )
        ).order_by(ChatMessage.created_at.desc()).first()

        unread = ChatMessage.query.filter_by(
            sender_id=u.id, receiver_id=current_user.id, is_read=False
        ).count()

        contacts.append({
            'id': u.id,
            'full_name': u.full_name or u.username,
            'initials': u.initials,
            'avatar': u.avatar,
            'status': u.online_status,
            'color': u.online_color,
            'last_message': last_msg.message[:50] if last_msg else '',
            'last_time': last_msg.created_at.isoformat() if last_msg else '',
            'unread': unread,
        })

    # Sort: unread first, then by last_time
    contacts.sort(key=lambda x: (x['unread'] == 0, x['last_time'] or ''), reverse=False)
    contacts.sort(key=lambda x: x['unread'], reverse=True)

    return jsonify(contacts)


@team_bp.route('/api/chat/messages/<int:user_id>')
@login_required
def chat_messages(user_id):
    """Lấy tin nhắn giữa current_user và user_id."""
    messages = ChatMessage.query.filter(
        or_(
            and_(ChatMessage.sender_id == current_user.id, ChatMessage.receiver_id == user_id),
            and_(ChatMessage.sender_id == user_id, ChatMessage.receiver_id == current_user.id),
        )
    ).order_by(ChatMessage.created_at.asc()).limit(100).all()

    # Mark as read
    ChatMessage.query.filter_by(
        sender_id=user_id, receiver_id=current_user.id, is_read=False
    ).update({'is_read': True, 'read_at': datetime.utcnow()})
    db.session.commit()

    return jsonify([{
        'id': m.id,
        'sender_id': m.sender_id,
        'message': m.message,
        'is_mine': m.sender_id == current_user.id,
        'is_read': m.is_read,
        'time': m.created_at.strftime('%H:%M'),
        'date': m.created_at.strftime('%d/%m/%Y'),
        'created_at': m.created_at.isoformat(),
    } for m in messages])


@team_bp.route('/api/chat/send', methods=['POST'])
@login_required
def chat_send():
    """Gửi tin nhắn."""
    data = request.json or {}
    receiver_id = data.get('receiver_id')
    message = data.get('message', '').strip()

    if not receiver_id or not message:
        return jsonify({'error': 'Missing data'}), 400

    msg = ChatMessage(
        tenant_id=current_user.tenant_id,
        sender_id=current_user.id,
        receiver_id=int(receiver_id),
        message=message,
    )
    db.session.add(msg)
    db.session.commit()

    return jsonify({
        'id': msg.id,
        'sender_id': msg.sender_id,
        'message': msg.message,
        'is_mine': True,
        'time': msg.created_at.strftime('%H:%M'),
        'created_at': msg.created_at.isoformat(),
    })


@team_bp.route('/api/chat/unread')
@login_required
def chat_unread():
    """Số tin chưa đọc."""
    count = ChatMessage.query.filter_by(
        receiver_id=current_user.id, is_read=False
    ).count()
    return jsonify({'unread': count})


# ============================================================
# ACTIVITY LOGGING HELPER
# ============================================================
def log_activity(action, module=None, description=None, target_type=None, target_id=None):
    """Ghi log hoạt động. Gọi từ các route khác."""
    from flask_login import current_user as cu
    if cu and cu.is_authenticated:
        activity = UserActivity(
            tenant_id=cu.tenant_id,
            user_id=cu.id,
            action=action,
            module=module,
            description=description,
            target_type=target_type,
            target_id=target_id,
            ip_address=request.remote_addr,
        )
        db.session.add(activity)
        db.session.commit()
