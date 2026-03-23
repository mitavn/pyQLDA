import os
from flask import Flask
from flask_login import LoginManager
from config import Config

login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure instance dir exists
    os.makedirs(os.path.join(app.root_path, 'instance'), exist_ok=True)
    os.makedirs(app.config.get('UPLOAD_FOLDER', 'uploads'), exist_ok=True)

    # Init extensions
    from models.user import db
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Vui lòng đăng nhập để tiếp tục.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        from models.user import User
        return User.query.get(int(user_id))

    # Register blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.contacts import contacts_bp
    from routes.companies import companies_bp
    from routes.deals import deals_bp
    from routes.activities import activities_bp
    from routes.settings import settings_bp
    from routes.api import api_bp
    from routes.departments import departments_bp
    from routes.quotes import quotes_bp
    from routes.products import products_bp
    from routes.team import team_bp
    from routes.employees import employees_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(contacts_bp)
    app.register_blueprint(companies_bp)
    app.register_blueprint(deals_bp)
    app.register_blueprint(activities_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(departments_bp)
    app.register_blueprint(quotes_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(team_bp)
    app.register_blueprint(employees_bp)

    # Template filters
    @app.template_filter('format_currency')
    def format_currency(value):
        if value is None:
            return '0'
        try:
            return '{:,.0f}'.format(float(value))
        except (ValueError, TypeError):
            return '0'

    @app.template_filter('format_date')
    def format_date(value):
        if value is None:
            return ''
        try:
            return value.strftime('%d/%m/%Y')
        except AttributeError:
            return str(value)

    @app.template_filter('format_datetime')
    def format_datetime(value):
        if value is None:
            return ''
        try:
            return value.strftime('%d/%m/%Y %H:%M')
        except AttributeError:
            return str(value)

    # Create tables
    with app.app_context():
        import models  # noqa - ensure all models loaded
        db.create_all()

    return app
