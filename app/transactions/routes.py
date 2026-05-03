from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import func, text, desc, extract
from app import db
from app.transactions import transactions
from app.transactions.forms import AddTransactionForm, FilterForm
from app.models import Transaction, BankAccount, Category, AccountType
from datetime import date


def get_user_account_ids():
    """Return list of account IDs belonging to the current user."""
    return [a.account_id for a in
            BankAccount.query.filter_by(user_id=current_user.user_id).all()]


@transactions.route('/', methods=['GET', 'POST'])
@login_required
def index():
    account_ids = get_user_account_ids()

    #Add Transaction form
    add_form = AddTransactionForm()
    user_accounts = BankAccount.query.filter_by(user_id=current_user.user_id).all()
    user_categories = Category.query.filter_by(user_id=current_user.user_id).all()

    add_form.account_id.choices = [
        (a.account_id, a.account_name) for a in user_accounts
    ]
    add_form.category_id.choices = [(0, 'No Category')] + [
        (c.category_id, c.name) for c in user_categories
    ]

    if add_form.validate_on_submit():
        txn = Transaction(
            account_id=add_form.account_id.data,
            category_id=add_form.category_id.data if add_form.category_id.data != 0 else None,
            transaction_type=add_form.transaction_type.data,
            amount=add_form.amount.data,
            transaction_date=add_form.transaction_date.data,
            description=add_form.description.data or None
        )
        db.session.add(txn)
        db.session.commit()
        flash('Transaction added successfully.', 'success')
        return redirect(url_for('transactions.index'))

    #Filter form
    filter_form = FilterForm()
    filter_form.account_id.choices = [(0, 'All Accounts')] + [
        (a.account_id, a.account_name) for a in user_accounts
    ]
    filter_form.category_id.choices = [(0, 'All Categories')] + [
        (c.category_id, c.name) for c in user_categories
    ]

    # Read filter values from query string
    f_account  = request.args.get('account_id',  0,  type=int)
    f_category = request.args.get('category_id', 0,  type=int)
    f_type     = request.args.get('transaction_type', '0')
    f_from     = request.args.get('date_from', '')
    f_to       = request.args.get('date_to', '')
    f_search   = request.args.get('search', '').strip()
    page       = request.args.get('page', 1, type=int)

    # Pre-fill filter form with current values
    filter_form.account_id.data  = f_account
    filter_form.category_id.data = f_category
    filter_form.transaction_type.data = f_type
    filter_form.search.data = f_search

    # Build query
    query = (
        db.session.query(Transaction, BankAccount.account_name, Category.name.label('category_name'))
        .join(BankAccount, Transaction.account_id == BankAccount.account_id)
        .outerjoin(Category, Transaction.category_id == Category.category_id)
        .filter(Transaction.account_id.in_(account_ids))
    )

    if f_account:
        query = query.filter(Transaction.account_id == f_account)
    if f_category:
        query = query.filter(Transaction.category_id == f_category)
    if f_type and f_type != '0':
        query = query.filter(Transaction.transaction_type == f_type)
    if f_from:
        query = query.filter(Transaction.transaction_date >= f_from)
    if f_to:
        query = query.filter(Transaction.transaction_date <= f_to)
    if f_search:
        query = query.filter(Transaction.description.ilike(f'%{f_search}%'))

    query = query.order_by(desc(Transaction.transaction_date))

    # Paginate — 25 per page
    pagination = query.paginate(page=page, per_page=25, error_out=False)
    txn_list   = pagination.items

    # ── Summary totals for filtered results ──────────────────────────
    base = db.session.query(Transaction).filter(Transaction.account_id.in_(account_ids))
    if f_account:  base = base.filter(Transaction.account_id == f_account)
    if f_category: base = base.filter(Transaction.category_id == f_category)
    if f_type and f_type != '0': base = base.filter(Transaction.transaction_type == f_type)
    if f_from: base = base.filter(Transaction.transaction_date >= f_from)
    if f_to:   base = base.filter(Transaction.transaction_date <= f_to)
    if f_search: base = base.filter(Transaction.description.ilike(f'%{f_search}%'))

    filtered_income = base.filter(
        Transaction.transaction_type == 'income'
    ).with_entities(func.coalesce(func.sum(Transaction.amount), 0)).scalar()

    filtered_expenses = base.filter(
        Transaction.transaction_type == 'expense'
    ).with_entities(func.coalesce(func.sum(Transaction.amount), 0)).scalar()

    return render_template(
        'transactions/index.html',
        add_form=add_form,
        filter_form=filter_form,
        txn_list=txn_list,
        pagination=pagination,
        filtered_income=filtered_income,
        filtered_expenses=filtered_expenses,
        f_account=f_account, f_category=f_category,
        f_type=f_type, f_from=f_from, f_to=f_to, f_search=f_search,
    )


# Insights route
@transactions.route('/insights')
@login_required
def insights():
    account_ids = get_user_account_ids()
    if not account_ids:
        flash('Add some accounts first to see insights.', 'info')
        return redirect(url_for('transactions.index'))

    ids_tuple = tuple(account_ids) if len(account_ids) > 1 else f"({account_ids[0]})"

    #  1. Monthly income vs expenses (last 12 months)
    monthly_summary = db.session.execute(text(f"""
        SELECT
            TO_CHAR(transaction_date, 'YYYY-MM') AS month,
            SUM(CASE WHEN transaction_type = 'income'  THEN amount ELSE 0 END) AS income,
            SUM(CASE WHEN transaction_type = 'expense' THEN amount ELSE 0 END) AS expenses,
            SUM(CASE WHEN transaction_type = 'income'  THEN amount
                     WHEN transaction_type = 'expense' THEN -amount ELSE 0 END) AS net
        FROM "transaction"
        WHERE account_id IN {ids_tuple}
          AND transaction_date >= CURRENT_DATE - INTERVAL '12 months'
        GROUP BY TO_CHAR(transaction_date, 'YYYY-MM')
        ORDER BY month
    """)).fetchall()

    # 2. Top 10 spending categories
    top_categories = db.session.execute(text(f"""
        SELECT
            COALESCE(c.name, 'Uncategorised') AS category,
            SUM(t.amount)                      AS total,
            COUNT(*)                           AS txn_count,
            ROUND(AVG(t.amount)::numeric, 2)   AS avg_amount
        FROM "transaction" t
        LEFT JOIN category c ON t.category_id = c.category_id
        WHERE t.account_id IN {ids_tuple}
          AND t.transaction_type = 'expense'
        GROUP BY c.name
        ORDER BY total DESC
        LIMIT 10
    """)).fetchall()

    # 3. Day-of-week spending pattern
    dow_spending = db.session.execute(text(f"""
        SELECT
            TO_CHAR(transaction_date, 'Day') AS day_name,
            EXTRACT(DOW FROM transaction_date) AS day_num,
            SUM(amount)   AS total_spent,
            COUNT(*)      AS txn_count,
            ROUND(AVG(amount)::numeric, 2) AS avg_spent
        FROM "transaction"
        WHERE account_id IN {ids_tuple}
          AND transaction_type = 'expense'
        GROUP BY day_name, day_num
        ORDER BY day_num
    """)).fetchall()

    # 4. Largest single transactions (top 10)
    largest_txns = db.session.execute(text(f"""
        SELECT
            t.transaction_date,
            t.description,
            t.amount,
            t.transaction_type,
            b.account_name,
            COALESCE(c.name, 'Uncategorised') AS category
        FROM "transaction" t
        JOIN bank_account b ON t.account_id = b.account_id
        LEFT JOIN category c ON t.category_id = c.category_id
        WHERE t.account_id IN {ids_tuple}
        ORDER BY t.amount DESC
        LIMIT 10
    """)).fetchall()

    # 5. Monthly spending trend per category (top 5 categories)
    top5_cats = db.session.execute(text(f"""
        SELECT COALESCE(c.name, 'Uncategorised') AS category
        FROM "transaction" t
        LEFT JOIN category c ON t.category_id = c.category_id
        WHERE t.account_id IN {ids_tuple}
          AND t.transaction_type = 'expense'
        GROUP BY c.name
        ORDER BY SUM(t.amount) DESC
        LIMIT 5
    """)).fetchall()
    top5_names = [r.category for r in top5_cats]

    category_monthly = db.session.execute(text(f"""
        SELECT
            TO_CHAR(t.transaction_date, 'YYYY-MM') AS month,
            COALESCE(c.name, 'Uncategorised')       AS category,
            SUM(t.amount)                           AS total
        FROM "transaction" t
        LEFT JOIN category c ON t.category_id = c.category_id
        WHERE t.account_id IN {ids_tuple}
          AND t.transaction_type = 'expense'
          AND COALESCE(c.name, 'Uncategorised') = ANY(:cats)
          AND t.transaction_date >= CURRENT_DATE - INTERVAL '12 months'
        GROUP BY month, category
        ORDER BY month, category
    """), {"cats": top5_names}).fetchall()

    # 6. Recurring merchant detection
    recurring = db.session.execute(text(f"""
        SELECT
            description,
            COUNT(*)                         AS occurrences,
            SUM(amount)                      AS total_spent,
            ROUND(AVG(amount)::numeric, 2)   AS avg_amount,
            MIN(transaction_date)            AS first_seen,
            MAX(transaction_date)            AS last_seen
        FROM "transaction"
        WHERE account_id IN {ids_tuple}
          AND transaction_type = 'expense'
          AND description IS NOT NULL
        GROUP BY description
        HAVING COUNT(*) >= 3
        ORDER BY total_spent DESC
        LIMIT 15
    """)).fetchall()

    # 7. Cumulative savings over time
    cumulative = db.session.execute(text(f"""
        SELECT
            transaction_date,
            SUM(
                CASE WHEN transaction_type = 'income'  THEN  amount
                     WHEN transaction_type = 'expense' THEN -amount
                     ELSE 0 END
            ) OVER (ORDER BY transaction_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
            AS running_balance
        FROM "transaction"
        WHERE account_id IN {ids_tuple}
        ORDER BY transaction_date
        LIMIT 365
    """)).fetchall()

    return render_template(
        'transactions/insights.html',
        monthly_summary=monthly_summary,
        top_categories=top_categories,
        dow_spending=dow_spending,
        largest_txns=largest_txns,
        category_monthly=category_monthly,
        top5_names=top5_names,
        recurring=recurring,
        cumulative=cumulative,
    )
