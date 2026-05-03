from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    user_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    accounts = db.relationship('BankAccount', backref='owner', lazy=True)
    goals = db.relationship('Goal', backref='user', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)
    verifications = db.relationship('Verification', backref='user', lazy=True)
    categories = db.relationship('Category', backref='user', lazy=True)
    budgets = db.relationship('Budget', backref='user', lazy=True)

    def get_id(self):
        return str(self.user_id)


class AccountType(db.Model):
    __tablename__ = 'account_type'
    account_type_id = db.Column(db.Integer, primary_key=True)
    type_name = db.Column(db.String(50), nullable=False)


class BankAccount(db.Model):
    __tablename__ = 'bank_account'
    account_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    account_type_id = db.Column(db.Integer, db.ForeignKey('account_type.account_type_id'))
    account_name = db.Column(db.String(100), nullable=False)
    current_balance = db.Column(db.Numeric(12, 2), default=0)
    credit_last4 = db.Column(db.String(4))
    transactions = db.relationship('Transaction', backref='account', lazy=True)


class Category(db.Model):
    __tablename__ = 'category'
    category_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    category_type = db.Column(db.String(50))


class Transaction(db.Model):
    __tablename__ = 'transaction'
    transaction_id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('bank_account.account_id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.category_id'))
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    transaction_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(255))
    transaction_type = db.Column(db.String(50))


class Budget(db.Model):
    __tablename__ = 'budget'
    budget_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.category_id'))
    monthly_limit = db.Column(db.Numeric(12, 2))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)


class Goal(db.Model):
    __tablename__ = 'goal'
    goal_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    goal_name = db.Column(db.String(150), nullable=False)
    target_amount = db.Column(db.Numeric(12, 2))
    current_amount = db.Column(db.Numeric(12, 2), default=0)
    deadline = db.Column(db.Date)


class Notification(db.Model):
    __tablename__ = 'notification'
    notification_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    message = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Verification(db.Model):
    __tablename__ = 'verification'
    verification_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    otp_code = db.Column(db.String(10))
    verification_type = db.Column(db.String(50))
    expiration_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='pending')