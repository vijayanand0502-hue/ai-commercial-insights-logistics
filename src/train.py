"""Train and compare the late delivery risk models.

Splits the clean data 80/20 (stratified on the target, grouped by order), trains two
baselines, a logistic regression and a lightly tuned HistGradientBoosting model,
tunes the decision threshold on out-of-fold training predictions, reports all
metrics on the test set, saves figures and the comparison table, and saves the
HistGradientBoosting pipeline with its tuned threshold.

Each row is one order item, so all metrics count order items, not orders.

Run from the project root:  python -m src.train
"""

from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.frozen import FrozenEstimator
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    RocCurveDisplay,
    accuracy_score,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import (
    FixedThresholdClassifier,
    GridSearchCV,
    StratifiedGroupKFold,
    cross_val_predict,
    cross_val_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from src.data_prep import load_processed
from src.features import build_preprocessor, get_feature_lists

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_FILE = PROJECT_ROOT / "models" / "model.joblib"
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"
COMPARISON_FILE = PROJECT_ROOT / "reports" / "model_comparison.csv"

TARGET = "late_delivery_risk"
GROUP = "order_id"
RANDOM_STATE = 42
CV_FOLDS = 5

# Small grid: 2 x 2 x 2 = 8 combinations, each scored with 5-fold CV.
TREE_PARAM_GRID = {
    "model__learning_rate": [0.05, 0.1],
    "model__max_leaf_nodes": [15, 31],
    "model__max_iter": [200, 400],
}

# Recall on "late" matters most: pick the highest threshold that still catches 80% of late items.
TARGET_RECALL = 0.80

MAJORITY = "Always late (baseline)"
SHIPPING_ONLY = "Shipping mode only (baseline)"
LOGISTIC = "Logistic regression"
TREE = "HistGradientBoosting"

ROC_COLORS = {LOGISTIC: "#2a78d6", TREE: "#eb6834", SHIPPING_ONLY: "#1baf7a"}


def make_group_folds(n_splits):
    """Folds that keep the late/on-time ratio and never split one order's items across folds."""
    return StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)


def split_train_test(df):
    """80/20 split: take one of 5 stratified, order-grouped folds as the test set."""
    train_idx, test_idx = next(make_group_folds(5).split(df, df[TARGET], groups=df[GROUP]))
    train, test = df.iloc[train_idx], df.iloc[test_idx]
    # No order may appear on both sides, or its items would leak from train into test.
    assert set(train[GROUP]).isdisjoint(test[GROUP])
    return train, test


def build_majority_baseline():
    """Baseline: predict the most common class ("late") for every item."""
    return DummyClassifier(strategy="most_frequent")


def build_shipping_mode_baseline():
    """Baseline: logistic regression on shipping_mode alone (learns the late rate per mode)."""
    prep = ColumnTransformer([("mode", OneHotEncoder(handle_unknown="ignore"), ["shipping_mode"])])
    return Pipeline([("prep", prep), ("model", LogisticRegression())])


def build_logistic_pipeline():
    """Baseline: one-hot + scaling, then logistic regression."""
    return Pipeline([
        ("prep", build_preprocessor("logistic")),
        ("model", LogisticRegression(max_iter=1000)),
    ])


def build_tree_pipeline():
    """Tree model: integer category codes, then HistGradientBoosting with native categorical support."""
    categorical, _ = get_feature_lists()
    model = HistGradientBoostingClassifier(
        categorical_features=categorical,
        # Early stopping would hold out a random (not order-grouped) 10% of training rows; max_iter is tuned instead.
        early_stopping=False,
        random_state=RANDOM_STATE,
    )
    return Pipeline([("prep", build_preprocessor("tree")), ("model", model)])


def choose_threshold(pipeline, X_train, y_train, groups, cv):
    """Pick the highest threshold whose out-of-fold recall on training data is >= TARGET_RECALL.

    Each training item is scored by a model that did not see it, so the test set is never used.
    """
    oof_prob = cross_val_predict(pipeline, X_train, y_train, groups=groups, cv=cv,
                                 method="predict_proba")[:, 1]
    _, recall, thresholds = precision_recall_curve(y_train, oof_prob)
    # recall has one more value than thresholds; recall falls as the threshold rises.
    meets_target = thresholds[recall[:-1] >= TARGET_RECALL]
    if len(meets_target) == 0:
        raise ValueError(f"No threshold reaches out-of-fold recall {TARGET_RECALL:.0%}")
    return meets_target.max()


def evaluate(pipeline, X_test, y_test):
    """Return test-set metrics, treating 'late' (1) as the positive class."""
    y_prob = pipeline.predict_proba(X_test)[:, 1]
    y_pred = pipeline.predict(X_test)  # threshold 0.5, or the tuned one for the saved model
    return {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred),
        "recall": recall_score(y_test, y_pred),
        "f1": f1_score(y_test, y_pred),
        "roc_auc": roc_auc_score(y_test, y_prob),
    }


def save_confusion_matrix(model, title, X_test, y_test):
    """Save the confusion matrix of one model to reports/figures/."""
    fig, ax = plt.subplots(figsize=(4.5, 4))
    ConfusionMatrixDisplay.from_estimator(
        model, X_test, y_test, display_labels=["On time", "Late"],
        cmap="Blues", colorbar=False, values_format=",", ax=ax,
    )
    ax.set_title(title)
    fig.savefig(FIGURES_DIR / "08_confusion_matrix.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def save_roc_curves(pipelines, X_test, y_test):
    """Save ROC curves of all models on one chart to reports/figures/."""
    fig, ax = plt.subplots(figsize=(5.5, 5))
    for name, color in ROC_COLORS.items():
        RocCurveDisplay.from_estimator(pipelines[name], X_test, y_test, name=name,
                                       curve_kwargs={"color": color, "linewidth": 2}, ax=ax)
    ax.plot([0, 1], [0, 1], color="#52514e", linestyle="--", linewidth=1, label="Random guess (AUC = 0.5)")
    ax.set_title("ROC curves (test set)")
    ax.legend(loc="lower right", frameon=False)
    fig.savefig(FIGURES_DIR / "09_roc_curves.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    """Split, train two baselines and two models, tune the HGB threshold, compare, save everything."""
    df = load_processed()
    train, test = split_train_test(df)
    # The target is removed from X explicitly; the preprocessor also drops ID and date columns.
    X_train, y_train = train.drop(columns=[TARGET]), train[TARGET]
    X_test, y_test = test.drop(columns=[TARGET]), test[TARGET]
    groups = train[GROUP]
    print(f"Train: {len(train):,} rows ({y_train.mean():.1%} late)   "
          f"Test: {len(test):,} rows ({y_test.mean():.1%} late)")

    # Same CV folds for every model, built from training data only.
    cv = make_group_folds(CV_FOLDS)

    pipelines = {
        MAJORITY: build_majority_baseline(),
        SHIPPING_ONLY: build_shipping_mode_baseline(),
        LOGISTIC: build_logistic_pipeline(),
    }
    cv_mean, cv_std = {}, {}
    for name, pipeline in pipelines.items():
        scores = cross_val_score(pipeline, X_train, y_train, groups=groups, cv=cv, scoring="roc_auc")
        cv_mean[name], cv_std[name] = scores.mean(), scores.std()
        pipeline.fit(X_train, y_train)

    search = GridSearchCV(build_tree_pipeline(), TREE_PARAM_GRID, cv=cv, scoring="roc_auc")
    search.fit(X_train, y_train, groups=groups)  # refits the best settings on all training data
    pipelines[TREE] = search.best_estimator_
    cv_mean[TREE] = search.best_score_
    cv_std[TREE] = search.cv_results_["std_test_score"][search.best_index_]
    print(f"{TREE} best settings: {search.best_params_}")

    # HistGradientBoosting is saved even though its CV ROC-AUC ties with logistic regression
    # (the gap is far smaller than the fold-to-fold spread): it keeps one column per
    # feature, so SHAP explanations map directly to features like shipping_mode.
    threshold = choose_threshold(pipelines[TREE], X_train, y_train, groups, cv)
    # FrozenEstimator stops FixedThresholdClassifier from retraining the already fitted pipeline.
    final_model = FixedThresholdClassifier(
        FrozenEstimator(pipelines[TREE]), threshold=threshold, response_method="predict_proba"
    ).fit(X_train, y_train)
    tuned_name = f"{TREE} (threshold {threshold:.2f})"
    print(f"Tuned threshold (out-of-fold recall >= {TARGET_RECALL:.0%}): {threshold:.3f}")

    rows = {}
    for name, pipeline in pipelines.items():
        rows[name] = {"cv_roc_auc": cv_mean[name], "cv_roc_auc_std": cv_std[name],
                      **evaluate(pipeline, X_test, y_test)}
    rows[tuned_name] = {"cv_roc_auc": cv_mean[TREE], "cv_roc_auc_std": cv_std[TREE],
                        **evaluate(final_model, X_test, y_test)}
    comparison = pd.DataFrame(rows).T.round(3)
    print("\nTest-set comparison (per order item, positive class = late, threshold 0.5 unless stated):")
    print(comparison.to_string())
    print("Note: the tuned row repeats the HGB ROC-AUC values because ROC-AUC does not depend on the threshold.")
    COMPARISON_FILE.parent.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(COMPARISON_FILE, index_label="model")

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    save_confusion_matrix(final_model, f"Confusion matrix: {tuned_name}\n(test set)", X_test, y_test)
    save_roc_curves(pipelines, X_test, y_test)

    MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(final_model, MODEL_FILE)
    print(f"\nSaved {tuned_name} -> {MODEL_FILE}")


if __name__ == "__main__":
    main()
