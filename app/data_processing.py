"""
database.py — every direct SQLite access for the whole app lives here:
schema creation, authentication, transaction CRUD, and budget storage.
Nothing outside this module should open a connection or write raw SQL.
"""

import calendar
import hashlib
import os
import secrets
import sqlite3
from datetime import date, datetime

from . import config

SAMPLE_DESCRIPTIONS = {
    "Housing": ["Rent"],
    "Food & Dining": ["Groceries", "Coffee shop", "Restaurant", "Lunch"],
    "Transportation": ["Gas", "Rideshare", "Transit pass", "Parking"],
    "Utilities": ["Electricity", "Internet", "Water bill", "Phone bill"],
    "Entertainment": ["Streaming", "Movies", "Concert tickets", "Video games"],
    "Health & Fitness": ["Gym membership", "Pharmacy", "Doctor visit"],
    "Shopping": ["Clothing", "Home goods", "Electronics"],
    "Personal Care": ["Haircut", "Toiletries"],
    "Other": ["Miscellaneous", "Gift"],
}


def _connect():
    os.makedirs(config.DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create tables if they don't exist yet, and seed a starter budget
    row for every expense category."""
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
            category TEXT NOT NULL,
            description TEXT,
            amount REAL NOT NULL CHECK (amount > 0),
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS budgets (
            category TEXT PRIMARY KEY,
            monthly_limit REAL NOT NULL DEFAULT 0
        )
        """
    )
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM budgets")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO budgets (category, monthly_limit) VALUES (?, ?)",
            list(config.DEFAULT_BUDGETS.items()),
        )
        conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
def _hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), 200_000
    )
    return digest.hex(), salt


def has_any_user():
    conn = _connect()
    n = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    return n > 0


def create_user(username, password):
    username = username.strip()
    if not username or not password:
        raise ValueError("Username and password are required.")
    pw_hash, salt = _hash_password(password)
    conn = _connect()
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash, salt, created_at) "
            "VALUES (?, ?, ?, ?)",
            (username, pw_hash, salt, datetime.now().isoformat(timespec="seconds")),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise ValueError("That username is already taken.")
    finally:
        conn.close()


def verify_user(username, password):
    conn = _connect()
    row = conn.execute(
        "SELECT password_hash, salt FROM users WHERE username = ?",
        (username.strip(),),
    ).fetchone()
    conn.close()
    if not row:
        return False
    stored_hash, salt = row
    check_hash, _ = _hash_password(password, salt)
    return secrets.compare_digest(stored_hash, check_hash)


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------
def add_transaction(tx_date, tx_type, category, description, amount):
    conn = _connect()
    conn.execute(
        "INSERT INTO transactions (date, type, category, description, amount, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            tx_date,
            tx_type,
            category,
            description,
            float(amount),
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    conn.commit()
    conn.close()


def delete_transaction(tx_id):
    conn = _connect()
    conn.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
    conn.commit()
    conn.close()


def fetch_all_transactions():
    conn = _connect()
    rows = conn.execute(
        "SELECT id, date, type, category, description, amount "
        "FROM transactions ORDER BY date DESC, id DESC"
    ).fetchall()
    conn.close()
    return rows


def clear_all_transactions():
    conn = _connect()
    conn.execute("DELETE FROM transactions")
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Budgets
# ---------------------------------------------------------------------------
def fetch_budgets():
    conn = _connect()
    rows = conn.execute("SELECT category, monthly_limit FROM budgets").fetchall()
    conn.close()
    return dict(rows)


def set_budget(category, monthly_limit):
    conn = _connect()
    conn.execute(
        "INSERT INTO budgets (category, monthly_limit) VALUES (?, ?) "
        "ON CONFLICT(category) DO UPDATE SET monthly_limit = excluded.monthly_limit",
        (category, float(monthly_limit)),
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Sample data — lets a new user explore the dashboard/reports immediately
# instead of staring at empty charts. Only ever additive; never runs
# automatically.
# ---------------------------------------------------------------------------
def _shift_month(year, month, delta):
    total = (year * 12 + (month - 1)) + delta
    y, m = divmod(total, 12)
    return y, m + 1


def seed_sample_data():
    import random

    rng = random.Random(7)
    today = date.today()
    now_iso = datetime.now().isoformat(timespec="seconds")

    expense_ranges = {
        "Housing": (1050, 1250, 1, 1),
        "Food & Dining": (15, 90, 8, 14),
        "Transportation": (20, 120, 3, 6),
        "Utilities": (40, 180, 2, 4),
        "Entertainment": (10, 75, 2, 5),
        "Health & Fitness": (15, 150, 1, 3),
        "Shopping": (20, 200, 2, 5),
        "Personal Care": (10, 60, 1, 3),
        "Other": (10, 50, 1, 2),
    }

    conn = _connect()
    cur = conn.cursor()

    for i in range(5, -1, -1):
        y, m = _shift_month(today.year, today.month, -i)
        days_in_month = calendar.monthrange(y, m)[1]
        max_day = days_in_month if i > 0 else max(1, today.day)

        cur.execute(
            "INSERT INTO transactions (date, type, category, description, amount, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                date(y, m, 1).isoformat(),
                "income",
                "Salary",
                "Monthly paycheck",
                round(rng.uniform(3400, 3900), 2),
                now_iso,
            ),
        )
        if rng.random() < 0.4 and max_day > 5:
            day = min(rng.randint(5, max_day), max_day)
            cur.execute(
                "INSERT INTO transactions (date, type, category, description, amount, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    date(y, m, day).isoformat(),
                    "income",
                    "Freelance",
                    "Side project payment",
                    round(rng.uniform(150, 700), 2),
                    now_iso,
                ),
            )

        for category, (low, high, min_n, max_n) in expense_ranges.items():
            count = rng.randint(min_n, max_n)
            descriptions = SAMPLE_DESCRIPTIONS.get(category, [category])
            for _ in range(count):
                day = min(rng.randint(1, max_day), max_day)
                amount = round(rng.uniform(low, high), 2)
                desc = rng.choice(descriptions)
                cur.execute(
                    "INSERT INTO transactions (date, type, category, description, amount, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (date(y, m, day).isoformat(), "expense", category, desc, amount, now_iso),
                )

    conn.commit()
    conn.close()
