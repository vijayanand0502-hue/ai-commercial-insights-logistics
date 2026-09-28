"""Tests for src/db.py.

Every test uses a temporary SQLite file (pytest's tmp_path), never data/app.db.
Orders come from a small 6-row CSV with the same 22 columns as orders_clean.csv.
"""

import sqlite3

import pandas as pd
import pytest

from src import db

# 6 order items across 3 regions: 3 in Central America, 2 in South Asia, 1 in Western Europe.
REGIONS = ["Central America", "Central America", "Central America", "South Asia", "South Asia", "Western Europe"]


def make_orders_csv(path):
    """Write a small orders CSV in the clean-CSV format and return its path."""
    n = len(REGIONS)
    df = pd.DataFrame({
        "payment_type": ["DEBIT"] * n,
        "scheduled_shipping_days": [4] * n,
        "late_delivery_risk": [0, 1, 0, 1, 1, 0],
        "category_name": ["Sporting Goods"] * n,
        "customer_city": ["Caguas"] * n,
        "customer_country": ["Puerto Rico"] * n,
        "customer_segment": ["Consumer"] * n,
        "customer_state": ["PR"] * n,
        "department_name": ["Fitness"] * n,
        "market": ["LATAM"] * n,
        "order_city": ["Town"] * n,
        "order_country": ["Country"] * n,
        "order_date": ["2018-01-31 22:56:00"] * n,
        "order_id": [1, 1, 2, 3, 4, 5],
        "discount_rate": [0.05] * n,
        "order_item_id": [101, 102, 103, 104, 105, 106],
        "product_price": [327.75] * n,
        "quantity": [1] * n,
        "order_region": REGIONS,
        "order_state": ["State"] * n,
        "product_name": ["Smart watch"] * n,
        "shipping_mode": ["Standard Class"] * n,
    })
    df.to_csv(path, index=False)
    return path


@pytest.fixture
def conn(tmp_path):
    """A fresh database with the tables created."""
    connection = db.get_connection(tmp_path / "test.db")
    db.init_db(connection)
    yield connection
    connection.close()


@pytest.fixture
def conn_with_orders(conn, tmp_path):
    """A fresh database with the 6 sample orders loaded."""
    db.load_orders(conn, csv_path=make_orders_csv(tmp_path / "orders.csv"))
    return conn


def table_names(conn):
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    return {row[0] for row in rows}


# ---------- init_db ----------

def test_init_db_creates_three_tables(conn):
    assert {"users", "orders", "predictions"} <= table_names(conn)


def test_init_db_twice_is_safe(conn):
    db.init_db(conn)  # second run must not fail or drop anything
    assert {"users", "orders", "predictions"} <= table_names(conn)


# ---------- passwords ----------

def test_hash_password_format_is_salt_dollar_hash():
    stored = db.hash_password("secret")
    salt, digest = stored.split("$")
    assert len(salt) == db.SALT_BYTES * 2  # hex: 2 characters per byte
    assert len(digest) > 0
    assert "secret" not in stored  # never plain text


def test_same_password_gives_different_hashes():
    assert db.hash_password("secret") != db.hash_password("secret")


def test_check_password_true_for_correct_password():
    assert db.check_password("secret", db.hash_password("secret")) is True


def test_check_password_false_for_wrong_password():
    assert db.check_password("wrong", db.hash_password("secret")) is False


# ---------- add_user and verify_user ----------

def test_verify_user_correct_login(conn):
    db.add_user(conn, "alice", "pw123", "analyst", "South Asia")
    assert db.verify_user(conn, "alice", "pw123") == {
        "username": "alice", "role": "analyst", "region": "South Asia"
    }


def test_password_is_not_stored_in_plain_text(conn):
    db.add_user(conn, "alice", "pw123", "analyst", "South Asia")
    stored = conn.execute("SELECT password_hash FROM users WHERE username = 'alice'").fetchone()[0]
    assert stored != "pw123"
    assert "pw123" not in stored


def test_verify_user_wrong_password_returns_none(conn):
    db.add_user(conn, "alice", "pw123", "analyst", "South Asia")
    assert db.verify_user(conn, "alice", "wrong") is None


def test_verify_user_unknown_user_returns_none(conn):
    assert db.verify_user(conn, "nobody", "pw123") is None


def test_verify_user_sql_injection_returns_none(conn):
    db.add_user(conn, "admin", "pw123", "admin", db.ALL_REGIONS)
    assert db.verify_user(conn, "admin' OR '1'='1", "anything") is None


def test_add_user_duplicate_username_raises(conn):
    db.add_user(conn, "alice", "pw123", "analyst", "South Asia")
    with pytest.raises(sqlite3.IntegrityError):
        db.add_user(conn, "alice", "other", "analyst", "South Asia")


def test_add_user_invalid_role_raises(conn):
    with pytest.raises(sqlite3.IntegrityError):
        db.add_user(conn, "bob", "pw123", "superuser", "South Asia")


# ---------- orders ----------

def test_load_orders_returns_row_count(conn, tmp_path):
    assert db.load_orders(conn, csv_path=make_orders_csv(tmp_path / "orders.csv")) == 6


def test_admin_sees_all_orders(conn_with_orders):
    orders = db.get_orders(conn_with_orders, "admin", db.ALL_REGIONS)
    assert len(orders) == 6


def test_analyst_sees_only_own_region(conn_with_orders):
    orders = db.get_orders(conn_with_orders, "analyst", "South Asia")
    assert len(orders) == 2
    assert set(orders["order_region"]) == {"South Asia"}


def test_analyst_with_region_all_sees_nothing(conn_with_orders):
    # Access is decided by role, so region text 'All' does not unlock every region.
    orders = db.get_orders(conn_with_orders, "analyst", db.ALL_REGIONS)
    assert len(orders) == 0


def test_get_orders_parses_order_date(conn_with_orders):
    orders = db.get_orders(conn_with_orders, "admin", db.ALL_REGIONS)
    assert pd.api.types.is_datetime64_any_dtype(orders["order_date"])


def test_load_orders_clears_predictions_and_reloads(conn_with_orders, tmp_path):
    db.save_prediction(conn_with_orders, 101, 0.7, "High")
    db.load_orders(conn_with_orders, csv_path=make_orders_csv(tmp_path / "orders2.csv"))
    assert len(db.get_predictions(conn_with_orders, "admin", db.ALL_REGIONS)) == 0
    assert len(db.get_orders(conn_with_orders, "admin", db.ALL_REGIONS)) == 6  # not doubled


# ---------- predictions ----------

def save_one_prediction_per_order(conn):
    for order_item_id in [101, 102, 103, 104, 105, 106]:
        db.save_prediction(conn, order_item_id, 0.5, "Medium")


def test_admin_sees_all_predictions(conn_with_orders):
    save_one_prediction_per_order(conn_with_orders)
    assert len(db.get_predictions(conn_with_orders, "admin", db.ALL_REGIONS)) == 6


def test_analyst_sees_only_own_region_predictions(conn_with_orders):
    save_one_prediction_per_order(conn_with_orders)
    predictions = db.get_predictions(conn_with_orders, "analyst", "Central America")
    assert len(predictions) == 3
    assert set(predictions["order_region"]) == {"Central America"}


def test_analyst_with_region_all_sees_no_predictions(conn_with_orders):
    save_one_prediction_per_order(conn_with_orders)
    assert len(db.get_predictions(conn_with_orders, "analyst", db.ALL_REGIONS)) == 0


def test_save_prediction_unknown_order_raises(conn_with_orders):
    with pytest.raises(sqlite3.IntegrityError):
        db.save_prediction(conn_with_orders, 999, 0.5, "Medium")


@pytest.mark.parametrize("bad_probability", [-0.1, 1.5])
def test_save_prediction_probability_outside_0_1_raises(conn_with_orders, bad_probability):
    with pytest.raises(sqlite3.IntegrityError):
        db.save_prediction(conn_with_orders, 101, bad_probability, "High")


# ---------- demo users ----------

def test_demo_users_without_env_vars_warn_and_use_defaults(conn, monkeypatch, capsys):
    monkeypatch.delenv("DEMO_ADMIN_PASSWORD", raising=False)
    monkeypatch.delenv("DEMO_ANALYST_PASSWORD", raising=False)
    db.create_demo_users(conn)
    output = capsys.readouterr().out
    assert "DEMO_ADMIN_PASSWORD" in output
    assert "DEMO_ANALYST_PASSWORD" in output
    assert db.verify_user(conn, "admin", "admin123")["role"] == "admin"
    assert db.verify_user(conn, "analyst", "analyst123")["region"] == db.ANALYST_REGION


def test_demo_users_with_env_vars_use_them_and_do_not_warn(conn, monkeypatch, capsys):
    monkeypatch.setenv("DEMO_ADMIN_PASSWORD", "admin-env-pw")
    monkeypatch.setenv("DEMO_ANALYST_PASSWORD", "analyst-env-pw")
    db.create_demo_users(conn)
    assert "Warning" not in capsys.readouterr().out
    assert db.verify_user(conn, "admin", "admin-env-pw") is not None
    assert db.verify_user(conn, "analyst", "analyst-env-pw") is not None
    assert db.verify_user(conn, "admin", "admin123") is None  # default no longer works


def test_demo_users_twice_does_not_duplicate(conn, monkeypatch):
    monkeypatch.delenv("DEMO_ADMIN_PASSWORD", raising=False)
    monkeypatch.delenv("DEMO_ANALYST_PASSWORD", raising=False)
    db.create_demo_users(conn)
    db.create_demo_users(conn)
    assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 2
