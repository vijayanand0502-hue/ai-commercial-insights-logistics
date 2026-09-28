"""SQLite database for the late delivery risk app.

Three tables:
  users        login accounts with a salted scrypt password hash, a role and a region
  orders       the cleaned order items from data/processed/orders_clean.csv
  predictions  model scores saved by the app, linked to orders by order_item_id

Every query uses "?" placeholders, never string formatting, so user input
cannot change the SQL (no SQL injection).

Run from the project root:  python -m src.db
"""

import hashlib
import hmac
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.data_prep import PROCESSED_FILE

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_FILE = PROJECT_ROOT / "data" / "app.db"

# An admin's region is stored as ALL_REGIONS and means "no region filter".
ALL_REGIONS = "All"

# Largest order_region by row count (27,174 of 172,762 rows).
ANALYST_REGION = "Central America"

# scrypt settings: n = CPU/memory cost, r = block size, p = parallelism.
# These are the commonly recommended interactive-login values (about 16 MB of memory per hash).
SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SALT_BYTES = 16

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL CHECK (role IN ('admin', 'analyst')),
    region        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    order_item_id           INTEGER PRIMARY KEY,
    order_id                INTEGER NOT NULL,
    order_date              TEXT NOT NULL,
    order_region            TEXT NOT NULL,
    order_country           TEXT NOT NULL,
    order_state             TEXT NOT NULL,
    order_city              TEXT NOT NULL,
    market                  TEXT NOT NULL,
    customer_segment        TEXT NOT NULL,
    customer_country        TEXT NOT NULL,
    customer_state          TEXT NOT NULL,
    customer_city           TEXT NOT NULL,
    department_name         TEXT NOT NULL,
    category_name           TEXT NOT NULL,
    product_name            TEXT NOT NULL,
    product_price           REAL NOT NULL,
    quantity                INTEGER NOT NULL,
    discount_rate           REAL NOT NULL,
    payment_type            TEXT NOT NULL,
    shipping_mode           TEXT NOT NULL,
    scheduled_shipping_days INTEGER NOT NULL,
    late_delivery_risk      INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_orders_region ON orders (order_region);

CREATE TABLE IF NOT EXISTS predictions (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    order_item_id    INTEGER NOT NULL REFERENCES orders (order_item_id),
    risk_probability REAL NOT NULL CHECK (risk_probability BETWEEN 0 AND 1),
    risk_level       TEXT NOT NULL,
    created_at       TEXT NOT NULL
);
"""


def get_connection(path=DB_FILE):
    """Open the database. SQLite only enforces foreign keys when this pragma is on."""
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn):
    """Create the tables if they do not exist yet."""
    conn.executescript(SCHEMA)
    conn.commit()


# ---------- passwords ----------

def hash_password(password):
    """Return 'salt$hash' (both hex). A new random salt per user means equal passwords get different hashes."""
    salt = os.urandom(SALT_BYTES)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P)
    return f"{salt.hex()}${digest.hex()}"


def check_password(password, stored_hash):
    """Re-hash the password with the stored salt and compare in constant time."""
    salt_hex, digest_hex = stored_hash.split("$")
    digest = hashlib.scrypt(
        password.encode("utf-8"), salt=bytes.fromhex(salt_hex), n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P
    )
    return hmac.compare_digest(digest.hex(), digest_hex)


# Checked against when the username does not exist, so an unknown user takes as long as a wrong password
# and response time does not reveal which usernames exist.
DUMMY_HASH = hash_password("not-a-real-password")


# ---------- users ----------

def add_user(conn, username, password, role, region):
    """Insert a new user. Raises sqlite3.IntegrityError if the username exists or the role is invalid."""
    conn.execute(
        "INSERT INTO users (username, password_hash, role, region) VALUES (?, ?, ?, ?)",
        (username, hash_password(password), role, region),
    )
    conn.commit()


def verify_user(conn, username, password):
    """Return {'username', 'role', 'region'} if the login is correct, otherwise None."""
    row = conn.execute(
        "SELECT username, password_hash, role, region FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    if row is None:
        check_password(password, DUMMY_HASH)  # same work as a real check; result ignored
        return None
    if not check_password(password, row[1]):
        return None
    return {"username": row[0], "role": row[2], "region": row[3]}


def create_demo_users(conn):
    """Add the admin and analyst demo accounts if they are missing. Passwords come from env vars."""
    demo_users = [
        ("admin", "DEMO_ADMIN_PASSWORD", "admin123", "admin", ALL_REGIONS),
        ("analyst", "DEMO_ANALYST_PASSWORD", "analyst123", "analyst", ANALYST_REGION),
    ]
    for username, env_var, default_password, role, region in demo_users:
        exists = conn.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone()
        if exists:
            continue
        password = os.environ.get(env_var)
        if password is None:
            print(f"Warning: {env_var} is not set; '{username}' gets the default demo password (docs/setup.md)")
            password = default_password
        add_user(conn, username, password, role, region)


# ---------- orders ----------

def load_orders(conn, csv_path=PROCESSED_FILE):
    """Replace the orders table contents with the processed CSV. Returns the number of rows loaded."""
    df = pd.read_csv(csv_path)
    conn.execute("DELETE FROM predictions")  # predictions point at orders, so clear them first
    conn.execute("DELETE FROM orders")
    # to_sql with if_exists="append" keeps our schema and inserts with placeholders.
    df.to_sql("orders", conn, if_exists="append", index=False)
    conn.commit()
    return len(df)


def get_orders(conn, role, region):
    """Return orders as a DataFrame. Admins see every region; anyone else only their own region.

    Access is decided by role, not by the region text, so a non-admin with region 'All' sees nothing.
    order_date is parsed to a datetime because the date features (month, weekday, quarter) need it.
    """
    if role == "admin":
        return pd.read_sql_query("SELECT * FROM orders", conn, parse_dates=["order_date"])
    return pd.read_sql_query(
        "SELECT * FROM orders WHERE order_region = ?", conn, params=(region,), parse_dates=["order_date"]
    )


# ---------- predictions ----------

def save_prediction(conn, order_item_id, risk_probability, risk_level):
    """Store one model score with a UTC timestamp."""
    conn.execute(
        "INSERT INTO predictions (order_item_id, risk_probability, risk_level, created_at) "
        "VALUES (?, ?, ?, ?)",
        (int(order_item_id), float(risk_probability), risk_level, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()


def get_predictions(conn, role, region):
    """Return saved predictions joined to their order's region, filtered the same way as get_orders."""
    query = (
        "SELECT p.id, p.order_item_id, o.order_region, p.risk_probability, p.risk_level, p.created_at "
        "FROM predictions p JOIN orders o ON o.order_item_id = p.order_item_id"
    )
    if role == "admin":
        return pd.read_sql_query(query, conn)
    return pd.read_sql_query(query + " WHERE o.order_region = ?", conn, params=(region,))


def main():
    """Build data/app.db: create tables, load orders, add demo users, print row counts."""
    conn = get_connection()
    init_db(conn)
    n_orders = load_orders(conn)
    create_demo_users(conn)

    n_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    n_analyst = conn.execute(
        "SELECT COUNT(*) FROM orders WHERE order_region = ?", (ANALYST_REGION,)
    ).fetchone()[0]
    conn.close()

    print(f"Database:             {DB_FILE}")
    print(f"Orders loaded:        {n_orders:,}")
    print(f"Users:                {n_users}")
    print(f"Analyst region:       {ANALYST_REGION} ({n_analyst:,} orders)")


if __name__ == "__main__":
    main()
