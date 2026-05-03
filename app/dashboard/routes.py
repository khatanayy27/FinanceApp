from flask import render_template
from flask_login import login_required, current_user
from sqlalchemy import func
from app import db
from app.dashboard import dashboard
from app.models import BankAccount, AccountType, Transaction


@dashboard.route('/')
@login_required
def index():
    # Get all the user's accounts with their account type info
    accounts = (db.session.query(BankAccount, AccountType.type_name)
                .outerjoin(AccountType, BankAccount.account_type_id == AccountType.account_type_id)
                .filter(BankAccount.user_id == current_user.user_id)
                .all())

    # Total balance across all accounts
    total_balance = sum(acc.current_balance for acc, _ in accounts) if accounts else 0

    # Get account IDs for transaction queries
    account_ids = [acc.account_id for acc, _ in accounts]

    # Total income (sum of all 'income' transactions)
    total_income = 0
    total_expenses = 0
    if account_ids:
        income_result = (db.session.query(func.sum(Transaction.amount))
                         .filter(Transaction.account_id.in_(account_ids))
                         .filter(Transaction.transaction_type == 'income')
                         .scalar())
        total_income = income_result or 0

        expense_result = (db.session.query(func.sum(Transaction.amount))
                          .filter(Transaction.account_id.in_(account_ids))
                          .filter(Transaction.transaction_type == 'expense')
                          .scalar())
        total_expenses = expense_result or 0

    net_worth = total_income - total_expenses

    return render_template(
        'dashboard/index.html',
        user=current_user,
        accounts=accounts,
        total_balance=total_balance,
        total_income=total_income,
        total_expenses=total_expenses,
        net_worth=net_worth,
    )

