"""
Banking App - Data Loader
=========================
Run this script from inside your PyCharm project terminal AFTER completing
Steps 1-7 (database created, models.py done, flask db upgrade done).

Usage:
    python load_data.py

Make sure your .env file has the correct DATABASE_URL before running.
"""

import os
import sys
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import sqlalchemy
from sqlalchemy import create_engine, text

# ── Load environment ──────────────────────────────────────────────────────────
load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found in .env file.")
    print("Make sure your .env contains: DATABASE_URL=postgresql://user:password@localhost/financedb")
    sys.exit(1)

# ── Data file paths ───────────────────────────────────────────────────────────
# Place all the .xls files in the same folder as this script,
# or update the paths below.
DATA_DIR = os.path.dirname(os.path.abspath(__file__))

FILES = {
    "account_type": os.path.join(DATA_DIR, "account_type.xls"),
    "users":        os.path.join(DATA_DIR, "users.xls"),
    "bank_account": os.path.join(DATA_DIR, "bank_account.xls"),
    "category":     os.path.join(DATA_DIR, "category.xls"),
    "transactions": os.path.join(DATA_DIR, "transactions.xls"),
    "budget":       os.path.join(DATA_DIR, "budget.xls"),
    "goal":         os.path.join(DATA_DIR, "goal.xls"),
    "notification": os.path.join(DATA_DIR, "notification.xls"),
    "verification": os.path.join(DATA_DIR, "verification.xls"),
}

# ── Connect ───────────────────────────────────────────────────────────────────
print("Connecting to database...")
try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("Connected successfully.\n")
except Exception as e:
    print(f"ERROR: Could not connect to the database.\n{e}")
    sys.exit(1)


# ── Helper ────────────────────────────────────────────────────────────────────
def load_csv(key):
    path = FILES[key]
    if not os.path.exists(path):
        print(f"  WARNING: File not found: {path}")
        return None
    df = pd.read_csv(path)
    print(f"  Loaded {len(df)} rows from {os.path.basename(path)}")
    return df


def insert(df, table_name, conn, if_exists="append"):
    """Insert a DataFrame into a PostgreSQL table."""
    try:
        df.to_sql(table_name, conn, if_exists=if_exists, index=False, method="multi")
        print(f"  ✓ Inserted {len(df)} rows into '{table_name}'")
    except Exception as e:
        print(f"  ✗ Error inserting into '{table_name}': {e}")
        raise


# ── Load order (respects foreign-key dependencies) ───────────────────────────
print("=" * 55)
print("Starting data load (order matters for foreign keys)")
print("=" * 55)

with engine.begin() as conn:

    # 1. account_type  (no FK dependencies)
    print("\n[1/9] account_type")
    df = load_csv("account_type")
    if df is not None:
        insert(df, "account_type", conn)

    # 2. user  (no FK dependencies)
    print("\n[2/9] user")
    df = load_csv("users")
    if df is not None:
        # Rename column to match the SQLAlchemy model if needed
        insert(df, "user", conn)

    # 3. bank_account  (FK → user, account_type)
    print("\n[3/9] bank_account")
    df = load_csv("bank_account")
    if df is not None:
        # Drop created_at if the model doesn't have it
        if "created_at" in df.columns:
            df = df.drop(columns=["created_at"])
        insert(df, "bank_account", conn)

    # 4. category  (FK → user)
    print("\n[4/9] category")
    df = load_csv("category")
    if df is not None:
        # Rename category_name → name to match model
        if "category_name" in df.columns:
            df = df.rename(columns={"category_name": "name"})
        insert(df, "category", conn)

    # 5. transaction  (FK → bank_account, category)
    print("\n[5/9] transaction")
    df = load_csv("transactions")
    if df is not None:
        insert(df, "transaction", conn)

    # 6. budget  (FK → user, category)
    print("\n[6/9] budget")
    df = load_csv("budget")
    if df is not None:
        # Rename monthly_limit if needed - keep as is, matches model
        insert(df, "budget", conn)

    # 7. goal  (FK → user)
    print("\n[7/9] goal")
    df = load_csv("goal")
    if df is not None:
        # Rename target_date → deadline to match model
        if "target_date" in df.columns:
            df = df.rename(columns={"target_date": "deadline"})
        # Drop status if model doesn't have it
        if "status" in df.columns:
            df = df.drop(columns=["status"])
        insert(df, "goal", conn)

    # 8. notification  (FK → user)
    print("\n[8/9] notification")
    df = load_csv("notification")
    if df is not None:
        # Keep only columns the model has
        keep = ["notification_id", "user_id", "message", "is_read", "created_at"]
        df = df[[c for c in keep if c in df.columns]]
        # Convert is_read to bool if needed
        if "is_read" in df.columns:
            df["is_read"] = df["is_read"].astype(bool)
        insert(df, "notification", conn)

    # 9. verification  (FK → user)
    print("\n[9/9] verification")
    df = load_csv("verification")
    if df is not None:
        # Rename columns to match model
        rename_map = {
            "pin_code":        "otp_code",
            "sent_time":       "expiration_time",   # closest match
            "expiration_time": "expiration_time",
            "verified_status": "status",
        }
        # Build only the columns that exist in the file
        new_cols = {}
        if "pin_code" in df.columns:
            new_cols["otp_code"] = df["pin_code"].astype(str)
        if "expiration_time" in df.columns:
            new_cols["expiration_time"] = df["expiration_time"]
        if "verified_status" in df.columns:
            # Map True/False → 'verified'/'pending'
            new_cols["status"] = df["verified_status"].map(
                {True: "verified", False: "pending", "True": "verified", "False": "pending"}
            ).fillna("pending")

        out = pd.DataFrame({
            "verification_id": df["verification_id"],
            "user_id":         df["user_id"],
            "verification_type": "email",   # default since not in file
            **new_cols,
        })
        insert(out, "verification", conn)

# ── Update sequences so future inserts get correct IDs ───────────────────────
print("\nUpdating PostgreSQL sequences...")
sequence_tables = [
    ("account_type", "account_type_id"),
    ("user",         "user_id"),
    ("bank_account", "account_id"),
    ("category",     "category_id"),
    ("transaction",  "transaction_id"),
    ("budget",       "budget_id"),
    ("goal",         "goal_id"),
    ("notification", "notification_id"),
    ("verification", "verification_id"),
]

with engine.begin() as conn:
    for table, pk in sequence_tables:
        try:
            conn.execute(text(
                f"SELECT setval(pg_get_serial_sequence('{table}', '{pk}'), "
                f"COALESCE(MAX({pk}), 1)) FROM \"{table}\""
            ))
            print(f"  ✓ Sequence updated for '{table}'")
        except Exception as e:
            print(f"  ✗ Could not update sequence for '{table}': {e}")

print("\n" + "=" * 55)
print("Data load complete!")
print("=" * 55)
print("\nYou can verify in pgAdmin:")
print("  → Expand financedb → Schemas → public → Tables")
print("  → Right-click any table → View/Edit Data → All Rows")
