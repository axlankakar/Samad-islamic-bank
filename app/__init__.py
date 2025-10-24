from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # Load configuration
    app.config.from_object('config.Config')
    
    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # Blueprints will be auth.login

    # Import and register blueprints
    from .routes.auth import auth_bp
    from .routes.admin import admin_bp
    # from .routes.user_management import user_management_bp # Placeholder for later
    # from .routes.transactions import transactions_bp # Placeholder for later
    # from .routes.profit_distribution import profit_distribution_bp # Placeholder for later

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    # app.register_blueprint(user_management_bp, url_prefix='/admin/users')
    # app.register_blueprint(transactions_bp, url_prefix='/admin/transactions')
    # app.register_blueprint(profit_distribution_bp, url_prefix='/admin/profit')

    @app.route('/')
    def index():
        return redirect(url_for('admin.dashboard'))

    with app.app_context():
        from . import models # Import models here to avoid circular imports
        db.create_all()  # Create database tables if they don't exist

        # Create a default admin user if one doesn't exist
        if not models.Admin.query.first():
            hashed_password = models.Admin.set_password('adminpassword') # You should change this
            admin_user = models.Admin(username='admin', password_hash=hashed_password)
            db.session.add(admin_user)
            db.session.commit()
            print("Default admin user created with username 'admin' and password 'adminpassword'")


    return app 