"""Train and compare the late delivery risk models.

Splits the clean data 80/20 (stratified on the target, grouped by order), trains a
logistic regression baseline and a lightly tuned HistGradientBoosting model, picks
the better one by cross-validated ROC-AUC on the training data, reports all metrics
on the test set, saves figures and the comparison table, and saves the best pipeline.

Run from the project root:  python -m src.train
"""

from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    RocCurveDisplay,
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GridSearchCV, StratifiedGroupKFold, cross_val_score
from sklearn.pipeline import Pipeline

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

MODEL_COLORS = {"Logistic regression": "#2a78d6", "HistGradientBoosting": "#eb6834"}


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


def evaluate(pipeline, X_test, y_test):
    """Return test-set metrics, treating 'late' (1) as the positive class."""
    y_prob = pipeline.predict_proba(X_test)[:, 1]
    y_pred = pipeline.predict(X_test)  # threshold 0.5
    return {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred),
        "recall": recall_score(y_test, y_pred),
        "f1": f1_score(y_test, y_pred),
        "roc_auc": roc_auc_score(y_test, y_prob),
    }


def save_confusion_matrix(pipeline, name, X_test, y_test):
    """Save the confusion matrix of one model to reports/figures/."""
    fig, ax = plt.subplots(figsize=(4.5, 4))
    ConfusionMatrixDisplay.from_estimator(
        pipeline, X_test, y_test, display_labels=["On time", "Late"],
        cmap="Blues", colorbar=False, values_format=",", ax=ax,
    )
    ax.set_title(f"Confusion matrix: {name} (test set)")
    fig.savefig(FIGURES_DIR / "08_confusion_matrix.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def save_roc_curves(pipelines, X_test, y_test):
    """Save ROC curves of all models on one chart to reports/figures/."""
    fig, ax = plt.subplots(figsize=(5.5, 5))
    for name, pipeline in pipelines.items():
        RocCurveDisplay.from_estimator(pipeline, X_test, y_test, name=name,
                                       color=MODEL_COLORS[name], linewidth=2, ax=ax)
    ax.plot([0, 1], [0, 1], color="#52514e", linestyle="--", linewidth=1, label="Random guess (AUC = 0.5)")
    ax.set_title("ROC curves (test set)")
    ax.legend(loc="lower right", frameon=False)
    fig.savefig(FIGURES_DIR / "09_roc_curves.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    """Split, train both models, compare, save figures, table and the best pipeline."""
    df = load_processed()
    train, test = split_train_test(df)
    # The target is removed from X explicitly; the preprocessor also drops ID and date columns.
    X_train, y_train = train.drop(columns=[TARGET]), train[TARGET]
    X_test, y_test = test.drop(columns=[TARGET]), test[TARGET]
    groups = train[GROUP]
    print(f"Train: {len(train):,} rows ({y_train.mean():.1%} late)   "
          f"Test: {len(test):,} rows ({y_test.mean():.1%} late)")

    # Same CV folds for both models, built from training data only.
    cv = make_group_folds(CV_FOLDS)

    logistic = build_logistic_pipeline()
    logistic_cv_auc = cross_val_score(logistic, X_train, y_train, groups=groups,
                                      cv=cv, scoring="roc_auc", n_jobs=-1).mean()
    logistic.fit(X_train, y_train)
    print(f"Logistic regression   CV ROC-AUC: {logistic_cv_auc:.3f}")

    search = GridSearchCV(build_tree_pipeline(), TREE_PARAM_GRID, cv=cv, scoring="roc_auc", n_jobs=-1)
    search.fit(X_train, y_train, groups=groups)  # refits the best settings on all training data
    tree = search.best_estimator_
    print(f"HistGradientBoosting  CV ROC-AUC: {search.best_score_:.3f}   best: {search.best_params_}")

    pipelines = {"Logistic regression": logistic, "HistGradientBoosting": tree}
    cv_scores = {"Logistic regression": logistic_cv_auc, "HistGradientBoosting": search.best_score_}

    # Choose on training CV, so the test set stays an unbiased final check.
    best_name = max(cv_scores, key=cv_scores.get)

    comparison = pd.DataFrame(
        {name: {"cv_roc_auc": cv_scores[name], **evaluate(p, X_test, y_test)} for name, p in pipelines.items()}
    ).T.round(3)
    print("\nTest-set comparison (positive class = late):")
    print(comparison.to_string())
    COMPARISON_FILE.parent.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(COMPARISON_FILE, index_label="model")

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    save_confusion_matrix(pipelines[best_name], best_name, X_test, y_test)
    save_roc_curves(pipelines, X_test, y_test)

    MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipelines[best_name], MODEL_FILE)
    print(f"\nBest model (by CV ROC-AUC): {best_name} -> saved to {MODEL_FILE}")


if __name__ == "__main__":
    main()
