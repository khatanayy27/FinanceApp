# 💳 Banking & Personal Finance Management App

A full-stack, database-backed web application built with Python and Flask that allows users to track their personal finances in one place. The focus is on storing, organising, and surfacing meaningful insights from structured financial data using PostgreSQL.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Database Schema](#database-schema)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Loading Sample Data](#loading-sample-data)
- [Running the App](#running-the-app)
- [SQL Insights](#sql-insights)
- [Security](#security)

---

## Overview

This application was built as a data and database project with an emphasis on relational database design, complex SQL querying, and surfacing meaningful financial insights from structured data. Users can register an account, add their bank accounts, log transactions, set monthly budgets per spending category, and track savings goals — all backed by a PostgreSQL relational database.

---

## Features

### Authentication
- Email and password registration with bcrypt password hashing
- Secure session-based login via Flask-Login
- All routes protected with `@login_required`
- CSRF protection on all forms via Flask-WTF

### Dashboard
- Summary cards showing total balance, income, expenses, and net cash flow
- Account cards displaying each bank account with live balance

### Bank Accounts
- View all accounts in a table and card layout
- Per-account income, expense totals, and transaction count
- Add new accounts via modal form
- Drill into any account to see its last 20 transactions
- Supports Checking, Savings, and Credit account types

### Transactions
- Full paginated transaction list (25 per page)
- Six simultaneous filters: account, category, type, date from, date to, keyword search
- Filters translate directly to dynamic SQL WHERE clauses
- Add new transactions via modal form
- Filtered income/expense summary updates in real time

### Transaction Insights (SQL Analytics)
Seven SQL-powered analyses of spending patterns:
1. Monthly income vs expenses — `TO_CHAR`, conditional `SUM(CASE WHEN)`
2. Top 10 spending categories — `LEFT JOIN`, `GROUP BY`, `ORDER BY SUM DESC`
3. Day-of-week spending pattern — `EXTRACT(DOW)`
4. Largest individual transactions — `ORDER BY amount DESC LIMIT`
5. Monthly spend per top 5 categories — multi-dimensional `GROUP BY`, `ANY()`
6. Recurring merchants — `HAVING COUNT(*) >= 3`
7. Cumulative running balance — SQL window function `SUM() OVER (...)`

### Budgets
- Set monthly spending limits per category with a date range
- Live progress bars showing % of budget used
- Colour-coded status: green (under 70%), amber (70–90%), red (90%+)
- Grouped bar chart comparing budget limit vs actual spending (Chart.js)

### Goals
- Set savings goals with a target amount and deadline
- Update saved amount with inline form per goal
- Days remaining countdown with overdue detection
- Horizontal bar chart comparing saved vs target per goal (Chart.js)

---

## Tech Stack

### Backend
| Library | Purpose |
|---|---|
| Python 3.11+ | Core programming language |
| Flask | Web framework — routing, templating, request handling |
| Flask-SQLAlchemy | ORM — maps Python classes to PostgreSQL tables |
| Flask-Migrate | Database schema migrations (Alembic) |
| Flask-Login | User session management and route protection |
| Flask-Bcrypt | Password hashing using bcrypt algorithm |
| Flask-Mail | Email sending for OTP verification |
| Flask-WTF | Form handling and CSRF protection |
| WTForms | Form field definitions and validators |
| psycopg2-binary | PostgreSQL driver |
| python-dotenv | Loads environment variables from `.env` file |
| email-validator | Email format validation in forms |

### Database
| Tool | Purpose |
|---|---|
| PostgreSQL 15+ | Relational database — chosen for window functions, ILIKE, TO_CHAR, EXTRACT |
| pgAdmin 4 | GUI for database management and inspection |

### Frontend
| Library | Purpose |
|---|---|
| Jinja2 | Server-side HTML templating (built into Flask) |
| Bootstrap 5.3 | Responsive CSS framework |
| Bootstrap Icons | Icon library |
| Chart.js | JavaScript charting for budgets and goals pages |

---

## Database Schema

The database has 8 tables with foreign key relationships enforcing referential integrity.

```
USER (root table)
├── BANK_ACCOUNT    (user_id FK, account_type_id FK)
│   └── TRANSACTION (account_id FK, category_id FK)
├── CATEGORY        (user_id FK)
│   ├── TRANSACTION (category_id FK)
│   └── BUDGET      (user_id FK, category_id FK)
├── GOAL            (user_id FK)
├── NOTIFICATION    (user_id FK)
└── VERIFICATION    (user_id FK)

ACCOUNT_TYPE ──── BANK_ACCOUNT (account_type_id FK)
```

### Key Design Decisions
- `transaction` has no direct `user_id` — it connects to the user indirectly through `bank_account`. Queries always join through `bank_account` to isolate user data.
- `account_type` is a lookup table to keep account type values consistent rather than storing free text.
- `budget` joins with `transaction` at query time to calculate live spend vs limit — the spent figure is never cached.

---

## Project Structure

```
FinanceApp/
├── app/
│   ├── __init__.py          # App factory — creates Flask app, registers blueprints
│   ├── models.py            # All SQLAlchemy models (8 tables)
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── routes.py        # /auth/register, /auth/login, /auth/logout
│   │   └── forms.py         # RegisterForm, LoginForm
│   ├── dashboard/
│   │   ├── __init__.py
│   │   └── routes.py        # / (home dashboard)
│   ├── accounts/
│   │   ├── __init__.py
│   │   ├── routes.py        # /accounts/, /accounts/<id>
│   │   └── forms.py         # AddAccountForm
│   ├── transactions/
│   │   ├── __init__.py
│   │   ├── routes.py        # /transactions/, /transactions/insights
│   │   └── forms.py         # AddTransactionForm, FilterForm
│   ├── budgets/
│   │   ├── __init__.py
│   │   ├── routes.py        # /budgets/
│   │   └── forms.py         # AddBudgetForm
│   ├── goals/
│   │   ├── __init__.py
│   │   ├── routes.py        # /goals/, /goals/update/<id>
│   │   └── forms.py         # AddGoalForm, UpdateGoalForm
│   ├── static/
│   │   ├── css/style.css
│   │   └── js/charts.js
│   └── templates/
│       ├── base.html
│       ├── auth/
│       │   ├── login.html
│       │   └── register.html
│       ├── dashboard/
│       │   └── index.html
│       ├── accounts/
│       │   ├── index.html
│       │   └── detail.html
│       ├── transactions/
│       │   ├── index.html
│       │   └── insights.html
│       ├── budgets/
│       │   └── index.html
│       └── goals/
│           └── index.html
├── migrations/              # Flask-Migrate auto-generated migration scripts
├── config.py                # App configuration loaded from .env
├── run.py                   # Application entry point
├── load_data.py             # One-time script to load sample data from Excel files
├── requirements.txt         # Python dependencies
└── .env                     # Secret environment variables (not committed to git)
```

---

## Setup & Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- pgAdmin 4
- PyCharm (recommended) or any Python IDE

### 1. Clone the repository and create a virtual environment

```bash
# In PyCharm: File → New Project → set virtualenv
# Or manually:
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Mac/Linux
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create the PostgreSQL database

Open pgAdmin, right-click Databases → Create → Database, and name it `financedb`.

### 4. Create the `.env` file

Create a file named `.env` in the project root:

```
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost/financedb
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-gmail-app-password
```

> **Note:** For `MAIL_PASSWORD`, use a Gmail App Password generated at myaccount.google.com/apppasswords — not your regular Gmail password.
>
> **Note:** If your PostgreSQL password contains special characters like `@`, URL-encode them: `@` becomes `%40`.

### 5. Initialise the database

```bash
flask db init
flask db migrate -m "initial tables"
flask db upgrade
```

After running these commands, all 8 tables will be created in `financedb`. You can verify in pgAdmin under Schemas → public → Tables.

---

## Loading Sample Data

The project includes a pre-generated dataset of 100 users with linked accounts, transactions, categories, budgets, and goals.

### Steps

1. Place `load_data.py` and all `.xls` data files in the same folder
2. Run the loader:

```bash
python load_data.py
```

The script loads tables in foreign-key order (parent tables before child tables) to avoid constraint violations:

```
account_type → user → bank_account → category → transaction → budget → goal → notification → verification
```

### Logging in as a sample user

The passwords in the sample data are hashed with an unknown algorithm. To log in as a loaded user, reset their password via the Flask shell:

```bash
flask shell
```

```python
from app import db, bcrypt
from app.models import User

emails = [
    'example@email.com',
    'another@email.com',
]

for email in emails:
    user = User.query.filter_by(email=email).first()
    if user:
        user.password_hash = bcrypt.generate_password_hash('testpass123').decode('utf-8')
        print(f'Updated: {email}')

db.session.commit()
exit()
```

---

## Running the App

```bash
flask run
```

Open your browser and go to **http://127.0.0.1:5000**

You will be redirected to the login page. Either register a new account or log in as a sample user (see above).

---

## SQL Insights

The Insights page at `/transactions/insights` runs 7 analytical SQL queries directly against PostgreSQL. These bypass the ORM and use `db.session.execute(text(...))` to access PostgreSQL-specific features.

| # | Insight | Key SQL Feature |
|---|---|---|
| 1 | Monthly income vs expenses | `TO_CHAR`, `SUM(CASE WHEN ...)`, `INTERVAL` |
| 2 | Top 10 spending categories | `LEFT JOIN`, `GROUP BY`, `COALESCE`, `LIMIT` |
| 3 | Day-of-week spending | `EXTRACT(DOW)` |
| 4 | Largest transactions | `ORDER BY amount DESC LIMIT 10` |
| 5 | Monthly spend per category | Multi-dimensional `GROUP BY`, `ANY()` |
| 6 | Recurring merchants | `HAVING COUNT(*) >= 3` |
| 7 | Cumulative running balance | `SUM() OVER (ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)` |

---

## Security

| Measure | Implementation |
|---|---|
| Password hashing | Flask-Bcrypt with bcrypt algorithm and random salt |
| CSRF protection | Flask-WTF token on every form submission |
| Session security | Signed session cookies using `SECRET_KEY` |
| SQL injection prevention | SQLAlchemy parameterised queries; raw SQL uses named parameters |
| Data isolation | Every query filters by `current_user.user_id` — users cannot access each other's data |
| Route protection | `@login_required` on all authenticated routes |
| Secret management | All credentials stored in `.env`, never in source code |

---

## Requirements

```
flask
flask-sqlalchemy
flask-migrate
flask-login
flask-bcrypt
flask-mail
flask-wtf
psycopg2-binary
python-dotenv
email-validator
```
