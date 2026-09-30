"""Tests for src/train.py.

The full training (grid search on 172k rows) is too slow for a test, so each function is
tested on a small synthetic dataset. The saved model is checked only if
models/model.joblib exists.
"""

import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import recall_score
from sklearn.model_selection import cross_val_predict

from src import train
from src.data_prep import PROCESSED_FILE
from src.features import CATEGORICAL_FEATURES, NUMERIC_FEATURES

# The 18 raw columns the app sends to the model (same as app.MODEL_INPUTS).
MODEL_INPUTS = CATEGORICAL_FEATURES + NUMERIC_FEATURES + ["order_date"]


def make_items(n_orders=100):
    """Order items for n_orders orders; order k has 1 to 3 items. Every 4th order is on time (0)."""
    rng = np.random.default_rng(0)
    rows = []
    for order_id in range(n_orders):
        target = 0 if order_id % 4 == 0 else 1
        for _ in range(order_id % 3 + 1):
            rows.append({"order_id": order_id, "late_delivery_risk": target, "x": target + rng.normal(0, 1)})
    return pd.DataFrame(rows)


# ---------- split_train_test ----------

def test_split_keeps_each_order_on_one_side():
    df = make_items()
    train_set, test_set = train.split_train_test(df)
    assert set(train_set["order_id"]).isdisjoint(test_set["order_id"])
    assert len(train_set) + len(test_set) == len(df)  # no row lost or duplicated


def test_split_test_share_is_about_20_percent():
    df = make_items()
    _, test_set = train.split_train_test(df)
    assert 0.15 <= len(test_set) / len(df) <= 0.25


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_split_with_fewer_than_5_orders_raises():
    df = make_items(n_orders=4)
    with pytest.raises(ValueError):
        train.split_train_test(df)


# ---------- choose_threshold ----------

def test_choose_threshold_meets_target_recall_out_of_fold():
    df = make_items(n_orders=200)
    X, y, groups = df[["x"]], df["late_delivery_risk"], df["order_id"]
    cv = train.make_group_folds(3)
    model = LogisticRegression()

    threshold = train.choose_threshold(model, X, y, groups, cv)

    # Recompute the same out-of-fold probabilities (same folds, same seed) and check recall.
    oof_prob = cross_val_predict(model, X, y, groups=groups, cv=cv, method="predict_proba")[:, 1]
    assert 0 < threshold < 1
    assert recall_score(y, oof_prob >= threshold) >= train.TARGET_RECALL


def test_choose_threshold_is_the_highest_that_meets_target():
    df = make_items(n_orders=200)
    X, y, groups = df[["x"]], df["late_delivery_risk"], df["order_id"]
    cv = train.make_group_folds(3)
    model = LogisticRegression()

    threshold = train.choose_threshold(model, X, y, groups, cv)

    oof_prob = cross_val_predict(model, X, y, groups=groups, cv=cv, method="predict_proba")[:, 1]
    next_higher = oof_prob[oof_prob > threshold].min()
    assert recall_score(y, oof_prob >= next_higher) < train.TARGET_RECALL


def test_choose_threshold_single_class_target_raises():
    # With no late items there is no recall to reach; the fit or the threshold search fails.
    df = make_items(n_orders=30)
    df["late_delivery_risk"] = 0
    with pytest.raises(ValueError):
        train.choose_threshold(LogisticRegression(), df[["x"]], df["late_delivery_risk"],
                               df["order_id"], train.make_group_folds(3))


# ---------- evaluate ----------

def test_evaluate_returns_expected_metric_keys_in_0_1():
    df = make_items()
    model = LogisticRegression().fit(df[["x"]], df["late_delivery_risk"])
    metrics = train.evaluate(model, df[["x"]], df["late_delivery_risk"])
    assert set(metrics) == {"accuracy", "precision", "recall", "f1", "roc_auc"}
    for value in metrics.values():
        assert 0 <= value <= 1


def test_evaluate_perfect_model_scores_1():
    X = pd.DataFrame({"x": [0.0, 0.1, 0.9, 1.0] * 5})
    y = pd.Series([0, 0, 1, 1] * 5)
    model = LogisticRegression(C=100).fit(X, y)
    metrics = train.evaluate(model, X, y)
    assert metrics["accuracy"] == metrics["recall"] == metrics["roc_auc"] == 1.0


@pytest.mark.filterwarnings("ignore::sklearn.exceptions.UndefinedMetricWarning")
def test_evaluate_single_class_test_set_gives_nan_roc_auc():
    # ROC-AUC needs both classes; scikit-learn 1.9 warns and returns NaN instead of raising.
    X = pd.DataFrame({"x": [0.0, 1.0]})
    model = LogisticRegression().fit(X, [0, 1])
    metrics = train.evaluate(model, X.iloc[[0, 0]], pd.Series([0, 0]))
    assert np.isnan(metrics["roc_auc"])


# ---------- baselines ----------

def test_majority_baseline_always_predicts_late():
    X = pd.DataFrame({"shipping_mode": ["Standard Class"] * 5})
    y = [1, 1, 1, 0, 0]  # late is the majority, as in the real data (about 55%)
    model = train.build_majority_baseline().fit(X, y)
    assert list(model.predict(X)) == [1, 1, 1, 1, 1]


def test_shipping_mode_baseline_learns_rate_per_mode_and_ignores_other_columns():
    X = pd.DataFrame({
        "shipping_mode": ["First Class"] * 10 + ["Standard Class"] * 10,
        "market": ["LATAM", "Europe"] * 10,
    })
    y = [1] * 10 + [0] * 10  # First Class always late, Standard Class always on time
    model = train.build_shipping_mode_baseline().fit(X, y)
    new = pd.DataFrame({"shipping_mode": ["First Class", "Standard Class"], "market": ["Africa", "Africa"]})
    assert list(model.predict(new)) == [1, 0]


def test_shipping_mode_baseline_unseen_mode_does_not_crash():
    X = pd.DataFrame({"shipping_mode": ["First Class", "Standard Class"] * 5})
    model = train.build_shipping_mode_baseline().fit(X, [1, 0] * 5)
    prob = model.predict_proba(pd.DataFrame({"shipping_mode": ["Drone"]}))[:, 1]
    assert 0 <= prob[0] <= 1


# ---------- saved model (skipped if not trained) ----------

@pytest.fixture(scope="module")
def saved_model():
    if not train.MODEL_FILE.exists() or not PROCESSED_FILE.exists():
        pytest.skip("models/model.joblib or orders_clean.csv missing")
    return joblib.load(train.MODEL_FILE)


def test_saved_model_threshold_is_tuned_value(saved_model):
    assert saved_model.threshold == pytest.approx(0.397, abs=0.001)


def test_saved_model_predicts_0_1_and_probabilities_from_18_inputs(saved_model):
    rows = pd.read_csv(PROCESSED_FILE, nrows=20, parse_dates=["order_date"])
    X = rows[MODEL_INPUTS]
    assert len(MODEL_INPUTS) == 18
    predictions = saved_model.predict(X)
    probabilities = saved_model.predict_proba(X)[:, 1]
    assert set(predictions) <= {0, 1}
    assert ((probabilities >= 0) & (probabilities <= 1)).all()
    # predict must agree with the tuned threshold
    assert list(predictions) == list((probabilities >= saved_model.threshold).astype(int))
