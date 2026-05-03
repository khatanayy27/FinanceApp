from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from config import Config
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
bcrypt = Bcrypt()
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    from app.auth import auth as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    from app.dashboard import dashboard as dash_bp
    app.register_blueprint(dash_bp)
    from app.accounts import accounts as accounts_bp
    app.register_blueprint(accounts_bp, url_prefix='/accounts')
    from app.transactions import transactions as transactions_bp
    app.register_blueprint(transactions_bp, url_prefix='/transactions')
    from app.budgets import budgets as budgets_bp
    app.register_blueprint(budgets_bp, url_prefix='/budgets')
    from app.goals import goals as goals_bp
    app.register_blueprint(goals_bp, url_prefix='/goals')
    app.jinja_env.globals['enumerate'] = enumerate
    
    return app
