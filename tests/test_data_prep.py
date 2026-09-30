"""Tests for src/data_prep.py.

Each step is tested on a tiny hand-made DataFrame with the same column names as the
raw DataCo CSV. The last test checks the real data/processed/orders_clean.csv and is
skipped if that file has not been created yet.
"""

import pandas as pd
import pytest

from src import data_prep
from src.data_prep import (
    KEEP_AND_RENAME,
    LEAKAGE_COLUMNS,
    PROCESSED_FILE,
    check_missing,
    drop_bad_states,
    drop_rows_and_columns,
    parse_dates,
    rename_columns,
    strip_text,
)

# Every column the pipeline drops (same lists that drop_rows_and_columns uses).
ALL_DROPPED_COLUMNS = (
    data_prep.LEAKAGE_COLUMNS
    + data_prep.UNCERTAIN_TIMING_COLUMNS
    + data_prep.PERSONAL_COLUMNS
    + data_prep.IDENTIFIER_COLUMNS
    + data_prep.DUPLICATE_COLUMNS
    + data_prep.NO_INFORMATION_COLUMNS
)


def make_raw(order_statuses):
    """A small raw-style DataFrame: one row per status, with every raw column the pipeline expects."""
    n = len(order_statuses)
    df = pd.DataFrame({column: ["x"] * n for column in ALL_DROPPED_COLUMNS + list(KEEP_AND_RENAME)})
    df["Order Status"] = order_statuses
    df["Order Id"] = range(1, n + 1)
    df["Order Item Id"] = range(101, 101 + n)
    df["Late_delivery_risk"] = [i % 2 for i in range(n)]
    df["Days for shipment (scheduled)"] = 4
    df["Order Item Product Price"] = 327.75
    df["Order Item Quantity"] = 1
    df["Order Item Discount Rate"] = 0.05
    df["order date (DateOrders)"] = "1/31/2018 22:56"
    df["Customer State"] = "PR"
    df["Order Region"] = " Oceania "  # extra spaces, as in the raw file
    return df


# ---------- drop_rows_and_columns ----------

def test_never_shipped_orders_are_removed():
    raw = make_raw(["COMPLETE", "CANCELED", "SUSPECTED_FRAUD", "PENDING"])
    result = drop_rows_and_columns(raw)
    assert len(result) == 2
    assert list(result["Order Id"]) == [1, 4]  # the COMPLETE and PENDING rows are kept


def test_leakage_columns_are_dropped():
    result = drop_rows_and_columns(make_raw(["COMPLETE"]))
    for column in LEAKAGE_COLUMNS:
        assert column not in result.columns


def test_only_approved_columns_remain_after_drop():
    result = drop_rows_and_columns(make_raw(["COMPLETE"]))
    assert set(result.columns) == set(KEEP_AND_RENAME)


def test_drop_rows_and_columns_missing_order_status_raises():
    raw = make_raw(["COMPLETE"]).drop(columns=["Order Status"])
    with pytest.raises(KeyError):
        drop_rows_and_columns(raw)


def test_kept_columns_never_overlap_dropped_columns():
    # A column cannot be both "kept as a feature" and "dropped for leakage".
    assert set(KEEP_AND_RENAME).isdisjoint(ALL_DROPPED_COLUMNS)


# ---------- strip_text ----------

def test_strip_text_removes_leading_and_trailing_spaces():
    df = pd.DataFrame({"market": [" Oceania ", "Oceania"], "quantity": [1, 2]})
    result = strip_text(df)
    assert list(result["market"]) == ["Oceania", "Oceania"]
    assert list(result["quantity"]) == [1, 2]  # numbers untouched


def test_strip_text_keeps_inner_spaces_and_does_not_change_input():
    df = pd.DataFrame({"shipping_mode": ["  Standard Class  "]})
    result = strip_text(df)
    assert result.loc[0, "shipping_mode"] == "Standard Class"
    assert df.loc[0, "shipping_mode"] == "  Standard Class  "  # original not mutated


# ---------- rename_columns ----------

def test_rename_columns_gives_snake_case_names():
    df = drop_rows_and_columns(make_raw(["COMPLETE"]))
    result = rename_columns(df)
    assert set(result.columns) == set(KEEP_AND_RENAME.values())
    assert "late_delivery_risk" in result.columns


def test_rename_columns_unapproved_column_raises():
    df = drop_rows_and_columns(make_raw(["COMPLETE"]))
    df["Delivery Status"] = "Late delivery"  # a leakage column sneaking back in
    with pytest.raises(ValueError, match="not in the approved list"):
        rename_columns(df)


def test_rename_columns_missing_column_raises():
    df = drop_rows_and_columns(make_raw(["COMPLETE"])).drop(columns=["Shipping Mode"])
    with pytest.raises(ValueError, match="missing from the data"):
        rename_columns(df)


# ---------- drop_bad_states ----------

def test_drop_bad_states_removes_zip_code_states():
    df = pd.DataFrame({"customer_state": ["PR", "95758", "CA", "91732"]})
    result = drop_bad_states(df)
    assert list(result["customer_state"]) == ["PR", "CA"]


def test_drop_bad_states_keeps_all_rows_when_none_are_bad():
    df = pd.DataFrame({"customer_state": ["PR", "CA"]})
    assert len(drop_bad_states(df)) == 2


# ---------- parse_dates ----------

def test_parse_dates_converts_raw_format():
    df = pd.DataFrame({"order_date": ["1/31/2018 22:56", "12/5/2017 7:03"]})
    result = parse_dates(df)
    assert result.loc[0, "order_date"] == pd.Timestamp(2018, 1, 31, 22, 56)
    assert result.loc[1, "order_date"] == pd.Timestamp(2017, 12, 5, 7, 3)


def test_parse_dates_does_not_change_input():
    df = pd.DataFrame({"order_date": ["1/31/2018 22:56"]})
    parse_dates(df)
    assert df.loc[0, "order_date"] == "1/31/2018 22:56"


def test_parse_dates_unexpected_format_raises():
    df = pd.DataFrame({"order_date": ["2018-31-01"]})
    with pytest.raises(ValueError):
        parse_dates(df)


# ---------- check_missing ----------

def test_check_missing_passes_on_complete_data():
    check_missing(pd.DataFrame({"a": [1, 2], "b": ["x", "y"]}))  # must not raise


def test_check_missing_raises_on_missing_value():
    df = pd.DataFrame({"a": [1, None], "b": ["x", "y"]})
    with pytest.raises(ValueError, match="Unexpected missing values"):
        check_missing(df)


# ---------- whole pipeline on the tiny frame ----------

def test_full_pipeline_on_small_raw_frame(tmp_path):
    raw = make_raw(["COMPLETE", "CANCELED", "CLOSED"])
    raw.loc[2, "Customer State"] = "95758"  # a shifted row
    df = rename_columns(strip_text(drop_rows_and_columns(raw)))
    df = drop_bad_states(parse_dates(df))
    check_missing(df)

    assert len(df) == 1  # CANCELED removed, bad state removed
    assert df.iloc[0]["order_region"] == "Oceania"

    # save and load back: order_date must come back as a datetime
    path = tmp_path / "clean.csv"
    data_prep.save_processed(df, path=path)
    loaded = data_prep.load_processed(path=path)
    assert pd.api.types.is_datetime64_any_dtype(loaded["order_date"])
    assert len(loaded) == 1


# ---------- the real processed file (skipped if not built) ----------

@pytest.fixture(scope="module")
def processed():
    if not PROCESSED_FILE.exists():
        pytest.skip("data/processed/orders_clean.csv not built yet")
    return pd.read_csv(PROCESSED_FILE)


def test_processed_file_is_clean(processed):
    snake_leakage = ["actual_shipping_days", "delivery_status", "shipping_date", "order_status"]
    for column in LEAKAGE_COLUMNS + snake_leakage:
        assert column not in processed.columns
    assert set(processed.columns) == set(KEEP_AND_RENAME.values())
    assert processed.isna().sum().sum() == 0
    assert processed["order_item_id"].is_unique
    assert set(processed["late_delivery_risk"].unique()) <= {0, 1}
