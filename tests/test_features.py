"""Tests for src/features.py.

Uses a small hand-made frame in the clean-CSV format. Each category appears at least
MIN_CATEGORY_COUNT (500) times, so the encoders keep them as real categories instead of
merging them into the "infrequent" group.
"""

import numpy as np
import pandas as pd
import pytest

from src.data_prep import KEEP_AND_RENAME, LEAKAGE_COLUMNS
from src.features import (
    MIN_CATEGORY_COUNT,
    add_date_features,
    build_preprocessor,
    get_feature_lists,
)


def make_orders(n=2 * MIN_CATEGORY_COUNT):
    """n clean order items: half 'Standard Class', half 'Same Day'; everything else constant."""
    half = n // 2
    return pd.DataFrame({
        "order_id": range(n),
        "order_item_id": range(1000, 1000 + n),
        "late_delivery_risk": [0, 1] * half,
        "scheduled_shipping_days": 4,
        "order_date": pd.to_datetime(["2018-01-01 10:00"] * half + ["2018-06-15 10:00"] * half),
        "payment_type": "DEBIT",
        "shipping_mode": ["Standard Class"] * half + ["Same Day"] * half,
        "customer_segment": "Consumer",
        "customer_country": "Puerto Rico",
        "customer_state": "PR",
        "customer_city": "Caguas",
        "market": "LATAM",
        "order_region": "Central America",
        "order_country": "Mexico",
        "order_state": "Jalisco",
        "order_city": "Guadalajara",
        "category_name": "Cleats",
        "department_name": "Apparel",
        "product_name": "Shoe",
        "product_price": np.linspace(10, 300, n),
        "quantity": [1, 2] * half,
        "discount_rate": 0.05,
    })


# ---------- add_date_features ----------

def test_add_date_features_known_dates():
    df = pd.DataFrame({"order_date": pd.to_datetime(["2018-01-01", "2017-12-31", "2018-07-04"])})
    result = add_date_features(df)
    # 2018-01-01 was a Monday, 2017-12-31 a Sunday, 2018-07-04 a Wednesday.
    assert list(result["order_month"]) == [1, 12, 7]
    assert list(result["order_weekday"]) == [0, 6, 2]
    assert list(result["order_quarter"]) == [1, 4, 3]


def test_add_date_features_does_not_change_input():
    df = pd.DataFrame({"order_date": pd.to_datetime(["2018-01-01"])})
    add_date_features(df)
    assert list(df.columns) == ["order_date"]


def test_add_date_features_text_date_raises():
    # order_date must already be a datetime (load_processed / get_orders parse it).
    df = pd.DataFrame({"order_date": ["2018-01-01"]})
    with pytest.raises(AttributeError):
        add_date_features(df)


# ---------- get_feature_lists (leakage check) ----------

def test_feature_lists_contain_no_leakage_target_or_id_columns():
    categorical, numeric = get_feature_lists()
    features = set(categorical + numeric)
    forbidden = set(LEAKAGE_COLUMNS) | {
        "actual_shipping_days", "delivery_status", "shipping_date", "order_status",
        "late_delivery_risk", "order_id", "order_item_id", "order_date",
        "scheduled_shipping_days",
    }
    assert features.isdisjoint(forbidden)


def test_feature_lists_only_use_approved_columns_or_date_parts():
    categorical, numeric = get_feature_lists()
    allowed = set(KEEP_AND_RENAME.values()) | {"order_month", "order_weekday", "order_quarter"}
    assert set(categorical + numeric) <= allowed


def test_feature_lists_have_no_duplicates_and_expected_size():
    categorical, numeric = get_feature_lists()
    assert len(categorical) == len(set(categorical)) == 17  # 14 categories + 3 date parts
    assert numeric == ["product_price", "quantity", "discount_rate"]


# ---------- build_preprocessor ----------

def test_logistic_preprocessor_handles_unseen_category_without_nan():
    orders = make_orders()
    prep = build_preprocessor("logistic").fit(orders)
    new = orders.head(2).copy()
    new["shipping_mode"] = "Drone"  # never seen in training
    result = prep.transform(new)
    dense = result.toarray() if hasattr(result, "toarray") else np.asarray(result)
    assert dense.shape[0] == 2
    assert not np.isnan(dense).any()


def test_tree_preprocessor_codes_unseen_category_as_minus_one():
    orders = make_orders()
    prep = build_preprocessor("tree").fit(orders)
    new = orders.head(2).copy()
    new["shipping_mode"] = "Drone"
    result = prep.transform(new)
    assert list(result["shipping_mode"]) == [-1, -1]
    assert set(prep.transform(orders)["shipping_mode"]) == {0, 1}  # seen modes get real codes


def test_tree_preprocessor_keeps_one_column_per_feature_and_drops_ids():
    categorical, numeric = get_feature_lists()
    result = build_preprocessor("tree").fit_transform(make_orders())
    assert list(result.columns) == categorical + numeric
    for column in ["order_id", "order_item_id", "late_delivery_risk", "order_date", "scheduled_shipping_days"]:
        assert column not in result.columns


def test_build_preprocessor_invalid_model_type_raises():
    with pytest.raises(ValueError, match="model_type"):
        build_preprocessor("forest")
