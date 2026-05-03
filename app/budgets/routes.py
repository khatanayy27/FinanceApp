from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import date
from app import db
from app.budgets import budgets
from app.budgets.forms import AddBudgetForm
from app.models import Budget, Category, Transaction, BankAccount


def get_user_account_ids():
    return [a.account_id for a in
            BankAccount.query.filter_by(user_id=current_user.user_id).all()]


@budgets.route('/', methods=['GET', 'POST'])
@login_required
def index():
    form = AddBudgetForm()
    user_categories = Category.query.filter_by(user_id=current_user.user_id).all()
    form.category_id.choices = [
        (c.category_id, c.name) for c in user_categories
    ]

    if form.validate_on_submit():
        new_budget = Budget(
            user_id=current_user.user_id,
            category_id=form.category_id.data,
            monthly_limit=form.monthly_limit.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data
        )
        db.session.add(new_budget)
        db.session.commit()
        flash('Budget added successfully.', 'success')
        return redirect(url_for('budgets.index'))

    account_ids = get_user_account_ids()

    # Fetch all budgets with category name and spending so far
    raw_budgets = (
        db.session.query(
            Budget,
            Category.name.label('category_name'),
            func.coalesce(
                func.sum(Transaction.amount), 0
            ).label('spent')
        )
        .join(Category, Budget.category_id == Category.category_id)
        .outerjoin(
            Transaction,
            (Transaction.category_id == Budget.category_id) &
            (Transaction.account_id.in_(account_ids)) &
            (Transaction.transaction_type == 'expense') &
            (Transaction.transaction_date >= Budget.start_date) &
            (Transaction.transaction_date <= Budget.end_date)
        )
        .filter(Budget.user_id == current_user.user_id)
        .group_by(Budget.budget_id, Category.name)
        .all()
    )

    # Build enriched budget list with progress %
    budget_list = []
    for row in raw_budgets:
        limit = float(row.Budget.monthly_limit)
        spent = float(row.spent)
        pct   = min(round((spent / limit * 100), 1) if limit > 0 else 0, 100)
        remaining = max(limit - spent, 0)
        status = (
            'danger'  if pct >= 90 else
            'warning' if pct >= 70 else
            'success'
        )
        is_active = (
            row.Budget.start_date <= date.today() <= row.Budget.end_date
        )
        budget_list.append({
            'budget':        row.Budget,
            'category_name': row.category_name,
            'spent':         spent,
            'limit':         limit,
            'remaining':     remaining,
            'pct':           pct,
            'status':        status,
            'is_active':     is_active,
        })

    # Data for Chart.js bar chart
    chart_labels  = [b['category_name'] for b in budget_list]
    chart_spent   = [b['spent']         for b in budget_list]
    chart_limits  = [b['limit']         for b in budget_list]

    total_budgeted = sum(b['limit'] for b in budget_list)
    total_spent    = sum(b['spent'] for b in budget_list)

    return render_template(
        'budgets/index.html',
        form=form,
        budget_list=budget_list,
        chart_labels=chart_labels,
        chart_spent=chart_spent,
        chart_limits=chart_limits,
        total_budgeted=total_budgeted,
        total_spent=total_spent,
    )