from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.accounts import accounts
from app.accounts.forms import AddAccountForm
from app.models import BankAccount, AccountType, Transaction
from sqlalchemy import func

@accounts.route('/', methods=['GET', 'POST'])
@login_required
def index():
    form = AddAccountForm()
    account_types = AccountType.query.all()
    form.account_type_id.choices = [
        (at.account_type_id, at.type_name) for at in account_types
    ]

    if form.validate_on_submit():
        new_account = BankAccount(
            user_id=current_user.user_id,
            account_name=form.account_name.data,
            account_type_id=form.account_type_id.data,
            current_balance=form.current_balance.data,
            credit_last4=form.credit_last4.data if form.credit_last4.data else None
        )
        db.session.add(new_account)
        db.session.commit()
        flash(f'Account "{form.account_name.data}" added successfully.', 'success')
        return redirect(url_for('accounts.index'))

    user_accounts = (
        db.session.query(
            BankAccount,
            AccountType.type_name,
            func.coalesce(func.sum(db.case(
                (Transaction.transaction_type == 'income', Transaction.amount),
                else_=0)), 0).label('total_income'),
            func.coalesce(func.sum(db.case(
                (Transaction.transaction_type == 'expense', Transaction.amount),
                else_=0)), 0).label('total_expenses'),
            func.count(Transaction.transaction_id).label('transaction_count')
        )
        .outerjoin(AccountType, BankAccount.account_type_id == AccountType.account_type_id)
        .outerjoin(Transaction, BankAccount.account_id == Transaction.account_id)
        .filter(BankAccount.user_id == current_user.user_id)
        .group_by(BankAccount.account_id, AccountType.type_name)
        .all()
    )

    total_balance = sum(row.BankAccount.current_balance
                        for row in user_accounts) if user_accounts else 0

    return render_template(
        'accounts/index.html',
        form=form,
        accounts=user_accounts,
        total_balance=total_balance,
        account_types=account_types,
    )

@accounts.route('/<int:account_id>')
@login_required
def account_detail(account_id):
    account = BankAccount.query.filter_by(
        account_id=account_id,
        user_id=current_user.user_id
    ).first_or_404()

    account_type = AccountType.query.get(account.account_type_id)

    recent_transactions = (
        Transaction.query
        .filter_by(account_id=account_id)
        .order_by(Transaction.transaction_date.desc())
        .limit(20)
        .all()
    )

    total_income = (db.session.query(func.sum(Transaction.amount))
                    .filter_by(account_id=account_id, transaction_type='income')
                    .scalar() or 0)

    total_expenses = (db.session.query(func.sum(Transaction.amount))
                      .filter_by(account_id=account_id, transaction_type='expense')
                      .scalar() or 0)

    return render_template(
        'accounts/detail.html',
        account=account,
        account_type=account_type,
        transactions=recent_transactions,
        total_income=total_income,
        total_expenses=total_expenses,
    )