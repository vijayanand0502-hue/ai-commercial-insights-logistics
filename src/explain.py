"""SHAP explanations for the late delivery risk model.

Global: which features matter most overall (bar chart of mean |SHAP| on test orders).
Local:  the top factors behind one order item's risk, in plain language.

SHAP values here explain the predicted probability of "late": the baseline is the
average risk over a background sample, and each value is a push in percentage points.

Why PermutationExplainer, not TreeExplainer: shap's TreeExplainer does not read
HistGradientBoosting's native categorical splits correctly (its values did not add
up to the model output, off by up to 3 log-odds). PermutationExplainer only calls the
model's predict function, so it is correct for any model; additivity is checked below.

Run from the project root:  python -m src.explain
"""

import calendar
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

from src.data_prep import load_processed
from src.features import add_date_features, get_feature_lists
from src.train import MODEL_FILE, TARGET, split_train_test

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GLOBAL_FIGURE = PROJECT_ROOT / "reports" / "figures" / "10_shap_global_importance.png"

BACKGROUND_SIZE = 100    # training rows that define the "average order" baseline
GLOBAL_SAMPLE_SIZE = 500  # test rows for the global plot (about 0.3 s per row)
RANDOM_STATE = 42


def load_pipeline(path=MODEL_FILE):
    """Load the saved model and return the inner preprocessing + HGB pipeline."""
    model = joblib.load(path)
    # Saved model = FixedThresholdClassifier(FrozenEstimator(pipeline)); SHAP needs the pipeline.
    return model.estimator_.estimator


def build_explainer(pipeline, background_orders):
    """Create a PermutationExplainer on the probability of "late".

    `background_orders` are rows in the clean-CSV format, normally a sample of training data.
    """
    prep, model = pipeline.named_steps["prep"], pipeline.named_steps["model"]
    background = prep.transform(background_orders)
    columns = background.columns

    def predict_late(encoded):
        # shap passes plain arrays; restore column names so the model sees what it was trained on.
        return model.predict_proba(pd.DataFrame(encoded, columns=columns))[:, 1]

    # shap applies the seed once, here in the constructor (np.random.seed, which also resets numpy's global
    # random state). A fresh explainer is repeatable; reusing one gives slightly different explanations per call.
    return shap.PermutationExplainer(predict_late, shap.maskers.Independent(background), seed=RANDOM_STATE)


def shap_values_for(orders, pipeline, explainer):
    """Return (encoded features, SHAP values, baseline) for rows in the clean-CSV format."""
    encoded = pipeline.named_steps["prep"].transform(orders)
    explanation = explainer(encoded, silent=True)
    values, baseline = explanation.values, explanation.base_values

    # Additivity: baseline + SHAP values must equal the model's predicted probability.
    predicted = pipeline.named_steps["model"].predict_proba(encoded)[:, 1]
    if not np.allclose(baseline + values.sum(axis=1), predicted, atol=1e-6):
        raise RuntimeError("SHAP values do not add up to the model's prediction")
    return encoded, values, baseline


def format_value(feature, value):
    """Show a feature's original value in a readable form."""
    if feature == "order_month":
        return calendar.month_name[int(value)]
    if feature == "order_weekday":
        return calendar.day_name[int(value)]
    if feature == "order_quarter":
        return f"Q{int(value)}"
    if feature == "discount_rate":
        return f"{value:.0%}"
    if feature == "product_price":
        return f"{value:.2f}"
    return str(value)


def rare_values(pipeline):
    """Return {feature: set of values} that the encoder merged into one "infrequent" group."""
    encoder = pipeline.named_steps["prep"].named_steps["columns"].named_transformers_["categorical"]
    return {
        feature: set(infrequent) if infrequent is not None else set()
        for feature, infrequent in zip(encoder.feature_names_in_, encoder.infrequent_categories_)
    }


def explain_order(order, pipeline, explainer, top_n=5):
    """Return up to top_n plain-language reasons for one order item's risk.

    `order` is a one-row DataFrame in the clean-CSV format. Features with a SHAP
    value of exactly 0 had no effect and are left out.
    """
    if len(order) != 1:
        raise ValueError(f"explain_order expects one row, got {len(order)}")

    encoded, values, _ = shap_values_for(order, pipeline, explainer)
    # Original values (not the encoded codes) are shown to the user.
    original = add_date_features(order).iloc[0]

    contributions = sorted(zip(encoded.columns, values[0]), key=lambda pair: abs(pair[1]), reverse=True)
    categorical, _ = get_feature_lists()
    rare = rare_values(pipeline)
    reasons = []
    for feature, shap_value in contributions[:top_n]:
        if shap_value == 0:
            continue
        label = feature.replace("_", " ").capitalize()
        value = format_value(feature, original[feature])
        if feature in categorical:
            value = f"'{value}'"
            # The model only saw "a rare value" here, not this specific one.
            if original[feature] in rare.get(feature, set()):
                value += " (a rare value, grouped with other rare values)"
        direction = "increased" if shap_value > 0 else "decreased"
        reasons.append(f"{label} {value} {direction} risk by {abs(shap_value) * 100:.1f} percentage points")
    return reasons


def save_global_summary(orders, pipeline, explainer, path=GLOBAL_FIGURE):
    """Save a bar chart of mean |SHAP| per feature (global importance)."""
    encoded, values, _ = shap_values_for(orders, pipeline, explainer)
    shap.summary_plot(values * 100, encoded, plot_type="bar", color="#2a78d6",
                      max_display=len(encoded.columns), show=False)
    plt.title(f"Global feature importance ({len(orders):,} test order items)")
    plt.xlabel("Mean |SHAP value| (percentage points of late risk)")
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()


def main():
    """Save the global plot and print explanations for one example order per shipping mode."""
    pipeline = load_pipeline()
    train, test = split_train_test(load_processed())
    background = train.drop(columns=[TARGET]).sample(BACKGROUND_SIZE, random_state=RANDOM_STATE)
    explainer = build_explainer(pipeline, background)

    sample = test.drop(columns=[TARGET]).sample(GLOBAL_SAMPLE_SIZE, random_state=RANDOM_STATE)
    save_global_summary(sample, pipeline, explainer)
    print(f"Saved global SHAP plot -> {GLOBAL_FIGURE}")

    for _, example in sample.groupby("shipping_mode").head(1).iterrows():
        order = example.to_frame().T.astype(sample.dtypes.to_dict())
        _, _, baseline = shap_values_for(order, pipeline, explainer)
        risk = pipeline.predict_proba(order)[0, 1]
        print(f"\nOrder item {order['order_item_id'].iloc[0]} ({order['shipping_mode'].iloc[0]}): "
              f"risk {risk:.0%} vs average {baseline[0]:.0%}")
        for reason in explain_order(order, pipeline, explainer):
            print(f"  - {reason}")


if __name__ == "__main__":
    main()
