"""Tests for src/explain.py (local SHAP explanations).

Skipped if the trained model file is missing. Orders are read through a temporary
database, so this also checks that rows coming from the DB have parseable dates.
"""

import pandas as pd
import pytest

from src import db, explain
from src.data_prep import PROCESSED_FILE
from src.train import MODEL_FILE, TARGET

if not MODEL_FILE.exists() or not PROCESSED_FILE.exists():
    pytest.skip("models/model.joblib or orders_clean.csv missing", allow_module_level=True)

N_ROWS = 51  # 50 background rows + 1 row to explain


@pytest.fixture(scope="module")
def setup(tmp_path_factory):
    """Load a small slice of the real processed CSV into a temp DB and read it back."""
    folder = tmp_path_factory.mktemp("explain")
    csv_path = folder / "orders_small.csv"
    pd.read_csv(PROCESSED_FILE, nrows=N_ROWS).to_csv(csv_path, index=False)

    conn = db.get_connection(folder / "test.db")
    db.init_db(conn)
    db.load_orders(conn, csv_path=csv_path)
    orders = db.get_orders(conn, "admin", db.ALL_REGIONS).drop(columns=[TARGET])
    conn.close()

    pipeline = explain.load_pipeline()  # already returns the inner HGB pipeline
    background = orders.iloc[:50]
    order = orders.iloc[[50]]  # double brackets keep it a one-row DataFrame
    return pipeline, background, order


def test_explain_order_returns_up_to_5_reasons(setup):
    pipeline, background, order = setup
    explainer = explain.build_explainer(pipeline, background)
    reasons = explain.explain_order(order, pipeline, explainer)
    assert isinstance(reasons, list)
    assert 0 < len(reasons) <= 5
    for reason in reasons:
        assert isinstance(reason, str)
        assert "percentage points" in reason


def test_fresh_explainers_give_identical_reasons(setup):
    pipeline, background, order = setup
    first = explain.explain_order(order, pipeline, explain.build_explainer(pipeline, background))
    second = explain.explain_order(order, pipeline, explain.build_explainer(pipeline, background))
    assert first == second


def test_explain_order_rejects_more_than_one_row(setup):
    pipeline, background, _ = setup
    explainer = explain.build_explainer(pipeline, background)
    with pytest.raises(ValueError):
        explain.explain_order(background.iloc[:2], pipeline, explainer)
