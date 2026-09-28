"""Feature engineering for the late delivery risk model.

Adds date parts from order_date, lists the final model inputs, and builds the
preprocessing step for each model type. Everything is a scikit-learn step, so it
is fitted inside the model Pipeline on training data only.

Usage in train.py:  Pipeline([("prep", build_preprocessor("logistic")), ("model", ...)])
"""

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, OrdinalEncoder, StandardScaler

# All known when the order is placed (see docs/data-dictionary.md).
# scheduled_shipping_days is left out: it maps one-to-one to shipping_mode (EDA charts 2 and 7).
CATEGORICAL_FEATURES = [
    "payment_type",
    "shipping_mode",
    "customer_segment",
    "customer_country",
    "customer_state",
    "customer_city",
    "market",
    "order_region",
    "order_country",
    "order_state",
    "order_city",
    "category_name",
    "department_name",
    "product_name",
]

# Treated as categories: month 12 is not "more" than month 1.
DATE_FEATURES = ["order_month", "order_weekday", "order_quarter"]

NUMERIC_FEATURES = ["product_price", "quantity", "discount_rate"]

# Categories seen fewer times than this in training are merged into one "infrequent" group.
# Keeps high-cardinality columns (e.g. 3,585 order cities) small and avoids noisy rare values.
# It also keeps every column under HistGradientBoosting's limit of 255 categories per feature
# (the largest is 57 today); recheck this if the dataset changes.
MIN_CATEGORY_COUNT = 500


def add_date_features(df):
    """Add month, weekday (0 = Monday) and quarter from order_date."""
    df = df.copy()
    df["order_month"] = df["order_date"].dt.month
    df["order_weekday"] = df["order_date"].dt.weekday
    df["order_quarter"] = df["order_date"].dt.quarter
    return df


def get_feature_lists():
    """Return (categorical, numeric) model input names; categorical includes the date parts."""
    return CATEGORICAL_FEATURES + DATE_FEATURES, NUMERIC_FEATURES


def build_preprocessor(model_type):
    """Build the unfitted preprocessing step for "logistic" or "tree" models.

    logistic: one-hot categories and scale numbers (a linear model needs both).
    tree:     one integer code per category (read by HistGradientBoosting's native
              categorical support) and raw numbers, so each feature stays one column.
    """
    categorical, numeric = get_feature_lists()

    if model_type == "logistic":
        encoder = OneHotEncoder(handle_unknown="infrequent_if_exist", min_frequency=MIN_CATEGORY_COUNT)
        numeric_step = StandardScaler()
    elif model_type == "tree":
        # Unseen categories become -1, which HistGradientBoosting treats as missing.
        encoder = OrdinalEncoder(
            handle_unknown="use_encoded_value", unknown_value=-1, min_frequency=MIN_CATEGORY_COUNT
        )
        numeric_step = "passthrough"
    else:
        raise ValueError(f"model_type must be 'logistic' or 'tree', got {model_type!r}")

    # remainder="drop" removes everything else: order_id, order_item_id, order_date and the target.
    columns = ColumnTransformer(
        [("categorical", encoder, categorical), ("numeric", numeric_step, numeric)],
        remainder="drop",
        verbose_feature_names_out=False,
    )
    if model_type == "tree":
        # Keep column names so the model can be told which columns are categorical by name.
        columns.set_output(transform="pandas")

    return Pipeline([
        ("date_features", FunctionTransformer(add_date_features)),
        ("columns", columns),
    ])
