from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from services.auth_service import authenticate, register_tenant

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = authenticate(username, password)
        if user:
            login_user(user, remember=True)
            next_page = request.args.get('next')
            flash('Đăng nhập thành công!', 'success')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            flash('Tên đăng nhập hoặc mật khẩu không đúng.', 'error')

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        tenant_name = request.form.get('tenant_name', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        full_name = request.form.get('full_name', '').strip()

        if not all([tenant_name, username, email, password]):
            flash('Vui lòng điền đầy đủ thông tin.', 'error')
        else:
            try:
                tenant, user = register_tenant(tenant_name, username, email, password, full_name)
                login_user(user)
                flash('Đăng ký thành công! Chào mừng bạn đến với CRM.', 'success')
                return redirect(url_for('dashboard.index'))
            except Exception as e:
                flash(f'Lỗi đăng ký: {str(e)}', 'error')

    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Đã đăng xuất.', 'info')
    return redirect(url_for('auth.login'))
