# Annexure: Printout of the Code
The source code below is copied automatically from the project files, one block per file.

## `src/__init__.py`
`src/__init__.py` is empty (it only marks `src` as a Python package).

## `src/data_prep.py`
201 lines.

````python
"""Data preparation for the late delivery risk project.

Loads the raw DataCo Smart Supply Chain CSV, removes orders that never shipped,
drops leakage, personal-data and redundant columns, tidies text and column names,
parses the order date, checks for missing values, and saves a clean CSV.

Run from the project root:  python -m src.data_prep
"""

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_FILE = PROJECT_ROOT / "data" / "raw" / "DataCoSupplyChainDataset.csv"
PROCESSED_FILE = PROJECT_ROOT / "data" / "processed" / "orders_clean.csv"

# The file is Windows-1252, not UTF-8; latin-1 would garble names like "Šiauliai".
RAW_ENCODING = "cp1252"

# Cancelled and suspected-fraud orders never shipped, so their "not late" label is meaningless.
NEVER_SHIPPED_STATUSES = ["CANCELED", "SUSPECTED_FRAUD"]

# Recorded after shipping or delivery; using them would leak the outcome.
LEAKAGE_COLUMNS = [
    "Days for shipping (real)",
    "Delivery Status",
    "shipping date (DateOrders)",
    "Order Status",
]

# Profit may include costs known only after delivery; excluded because the timing is uncertain.
UNCERTAIN_TIMING_COLUMNS = [
    "Benefit per order",
    "Order Profit Per Order",
    "Order Item Profit Ratio",
]

# Personal data or precise locations; city, state and region already describe location.
PERSONAL_COLUMNS = [
    "Customer Fname",
    "Customer Lname",
    "Customer Street",
    "Customer Zipcode",
    "Customer Email",
    "Customer Password",
    "Latitude",
    "Longitude",
]

# Numeric codes that duplicate a name column (or each other) and carry no extra meaning.
IDENTIFIER_COLUMNS = [
    "Customer Id",
    "Order Customer Id",
    "Product Card Id",
    "Order Item Cardprod Id",
    "Category Id",
    "Product Category Id",
    "Department Id",
]

# Exact copies or exact formulas of columns we keep.
DUPLICATE_COLUMNS = [
    "Product Price",        # same as Order Item Product Price
    "Sales per customer",   # same as Order Item Total
    "Sales",                # equals price x quantity
    "Order Item Total",     # equals price x quantity - discount
    "Order Item Discount",  # equals price x quantity x discount rate
]

# Empty, mostly empty, constant, or a URL.
NO_INFORMATION_COLUMNS = [
    "Product Description",  # 100% missing
    "Order Zipcode",        # 86% missing
    "Product Status",       # always 0
    "Product Image",        # image URL
]

# Every column we keep, with a short snake_case name that is easy to use in code and SQL.
KEEP_AND_RENAME = {
    "Order Id": "order_id",                      # database key and split group, not a feature
    "Order Item Id": "order_item_id",            # database key, not a feature
    "Late_delivery_risk": "late_delivery_risk",  # target
    "Type": "payment_type",
    "Days for shipment (scheduled)": "scheduled_shipping_days",
    "Shipping Mode": "shipping_mode",
    "order date (DateOrders)": "order_date",
    "Customer Segment": "customer_segment",
    "Customer Country": "customer_country",
    "Customer State": "customer_state",
    "Customer City": "customer_city",
    "Market": "market",
    "Order Region": "order_region",
    "Order Country": "order_country",
    "Order State": "order_state",
    "Order City": "order_city",
    "Category Name": "category_name",
    "Department Name": "department_name",
    "Product Name": "product_name",
    "Order Item Product Price": "product_price",
    "Order Item Quantity": "quantity",
    "Order Item Discount Rate": "discount_rate",
}


def load_raw(path=RAW_FILE):
    """Read the raw DataCo CSV with the correct encoding."""
    return pd.read_csv(path, encoding=RAW_ENCODING)


def drop_rows_and_columns(df):
    """Remove never-shipped orders, then drop every approved column."""
    # Filter rows first, because Order Status is itself dropped below.
    df = df[~df["Order Status"].isin(NEVER_SHIPPED_STATUSES)]
    columns_to_drop = (
        LEAKAGE_COLUMNS
        + UNCERTAIN_TIMING_COLUMNS
        + PERSONAL_COLUMNS
        + IDENTIFIER_COLUMNS
        + DUPLICATE_COLUMNS
        + NO_INFORMATION_COLUMNS
    )
    return df.drop(columns=columns_to_drop)


def strip_text(df):
    """Remove leading/trailing spaces so 'Oceania ' and 'Oceania' are one category."""
    df = df.copy()
    for column in df.select_dtypes(include=["object", "string"]).columns:
        df[column] = df[column].str.strip()
    return df


def rename_columns(df):
    """Rename kept columns to snake_case; fail if a column is unreviewed or missing."""
    unexpected = set(df.columns) - set(KEEP_AND_RENAME)
    if unexpected:
        # Guards against a column slipping into the features without a leakage review.
        raise ValueError(f"Columns not in the approved list: {sorted(unexpected)}")
    missing = set(KEEP_AND_RENAME) - set(df.columns)
    if missing:
        # rename() would silently skip these, so fail here instead of later.
        raise ValueError(f"Approved columns missing from the data: {sorted(missing)}")
    return df.rename(columns=KEEP_AND_RENAME)


def drop_bad_states(df):
    """Drop rows whose customer_state is a zip code (shifted rows in the raw file)."""
    # Their other columns may be shifted too, so we drop them rather than guess the state.
    return df[~df["customer_state"].str.isdigit()]


def parse_dates(df):
    """Convert order_date from text like '1/31/2018 22:56' to a datetime."""
    df = df.copy()
    # An explicit format is faster and fails loudly on unexpected values.
    df["order_date"] = pd.to_datetime(df["order_date"], format="%m/%d/%Y %H:%M")
    return df


def check_missing(df):
    """Fail if any value is missing (none are expected)."""
    # All columns that had gaps were dropped above, so silently dropping rows would hide a problem.
    missing_counts = df.isna().sum()
    if missing_counts.any():
        raise ValueError(f"Unexpected missing values:\n{missing_counts[missing_counts > 0]}")


def save_processed(df, path=PROCESSED_FILE):
    """Save the clean data as a UTF-8 CSV in data/processed/."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def load_processed(path=PROCESSED_FILE):
    """Read the clean CSV; CSV stores dates as text, so order_date is parsed again here."""
    return pd.read_csv(path, parse_dates=["order_date"])


def main():
    """Run the full preparation pipeline and print row counts at each step."""
    df = load_raw()
    print(f"Loaded:               {len(df):,} rows, {df.shape[1]} columns")

    df = drop_rows_and_columns(df)
    print(f"After drops:          {len(df):,} rows, {df.shape[1]} columns")

    df = rename_columns(strip_text(df))
    df = parse_dates(df)

    rows_before = len(df)
    df = drop_bad_states(df)
    print(f"Bad-state rows removed: {rows_before - len(df)}")

    check_missing(df)
    save_processed(df)
    print(f"Saved:                {len(df):,} rows, {df.shape[1]} columns -> {PROCESSED_FILE}")


if __name__ == "__main__":
    main()
````

## `src/db.py`
256 lines.

````python
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


def save_predictions(conn, order_item_ids, risk_probabilities, risk_levels):
    """Store many model scores in one transaction: all rows are saved, or none if any row fails."""
    created_at = datetime.now(timezone.utc).isoformat()
    rows = [
        (int(item_id), float(prob), level, created_at)
        for item_id, prob, level in zip(order_item_ids, risk_probabilities, risk_levels)
    ]
    # "with conn" commits if the block succeeds and rolls back if it raises, so a failed batch
    # leaves no half-saved rows behind on this connection.
    with conn:
        conn.executemany(
            "INSERT INTO predictions (order_item_id, risk_probability, risk_level, created_at) "
            "VALUES (?, ?, ?, ?)",
            rows,
        )


def count_predictions(conn):
    """Return how many predictions are stored."""
    return conn.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]


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
````

## `src/explain.py`
166 lines.

````python
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
````

## `src/features.py`
93 lines.

````python
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
````

## `src/train.py`
239 lines.

````python
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
````

## `app.py`
349 lines.

````python
"""Streamlit app for late delivery risk.

Screens: login, risk dashboard, single-order risk checker (with SHAP reasons) and
batch CSV scoring. Admins see every region; analysts only see their own region.

Run from the project root (after python -m src.db):  .venv/bin/streamlit run app.py
"""

from datetime import date

import joblib
import numpy as np
import pandas as pd
import streamlit as st

from src import db
from src.data_prep import PROCESSED_FILE, load_processed
from src.explain import BACKGROUND_SIZE, RANDOM_STATE, build_explainer, explain_order
from src.features import CATEGORICAL_FEATURES, NUMERIC_FEATURES
from src.train import MODEL_FILE, TARGET, split_train_test

# The raw columns the model needs; date parts are made from order_date inside the pipeline.
MODEL_INPUTS = CATEGORICAL_FEATURES + NUMERIC_FEATURES + ["order_date"]
HIGH, LOW = "High", "Low"
TOP_ORDERS = 20

st.set_page_config(page_title="Late Delivery Risk", layout="wide")


# ---------- loading (cached once per app process) ----------

@st.cache_resource
def load_model():
    """The saved model: HGB pipeline wrapped with its tuned threshold (0.397)."""
    return joblib.load(MODEL_FILE)


@st.cache_data
def load_background():
    """The 100 training rows SHAP compares against (same sample as src/explain.py)."""
    train, _ = split_train_test(load_processed())
    return train.drop(columns=[TARGET]).sample(BACKGROUND_SIZE, random_state=RANDOM_STATE)


@st.cache_data
def load_orders_for(role, region):
    """Orders this user may see. Cached per (role, region), so users never share each other's rows."""
    conn = db.get_connection()  # one connection per call: SQLite connections can't be shared across threads
    try:
        return db.get_orders(conn, role, region)
    finally:
        conn.close()


def load_predictions_for(role, region):
    conn = db.get_connection()
    try:
        return db.get_predictions(conn, role, region)
    finally:
        conn.close()


def score(model, orders):
    """Return (probability of late, risk level) for each row. The level uses the model's own threshold."""
    probabilities = model.predict_proba(orders[MODEL_INPUTS])[:, 1]
    levels = [HIGH if late == 1 else LOW for late in model.predict(orders[MODEL_INPUTS])]
    return probabilities, levels


def ensure_predictions(model):
    """Score every stored order once and save the results (again after the database is rebuilt)."""
    conn = db.get_connection()
    try:
        if db.count_predictions(conn) == 0:
            orders = load_orders_for("admin", db.ALL_REGIONS)
            probabilities, levels = score(model, orders)
            db.save_predictions(conn, orders["order_item_id"], probabilities, levels)
    finally:
        conn.close()


# ---------- login ----------

def show_login():
    st.title("Late Delivery Risk")
    with st.form("login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in")
    if submitted:
        conn = db.get_connection()
        try:
            user = db.verify_user(conn, username, password)
        finally:
            conn.close()
        if user is None:
            st.error("Wrong username or password.")  # same message for both, so usernames are not revealed
        else:
            st.session_state["user"] = user
            st.rerun()


# ---------- dashboard ----------

def show_dashboard(user):
    st.header("Risk dashboard")
    orders = load_orders_for(user["role"], user["region"])
    predictions = load_predictions_for(user["role"], user["region"])

    # Admins can narrow down to one region; an analyst's data is already limited by the SQL query.
    if user["role"] == "admin":
        choice = st.selectbox("Region", ["All regions"] + sorted(orders["order_region"].unique()))
        if choice != "All regions":
            orders = orders[orders["order_region"] == choice]
            predictions = predictions[predictions["order_region"] == choice]
    else:
        st.write(f"Region: **{user['region']}**")

    data = orders.merge(predictions[["order_item_id", "risk_probability", "risk_level"]], on="order_item_id")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Order items", f"{len(data):,}")
    col2.metric("Actual late rate", f"{data['late_delivery_risk'].mean():.1%}")
    col3.metric("Predicted high risk", f"{(data['risk_level'] == HIGH).mean():.1%}")
    col4.metric("Average predicted risk", f"{data['risk_probability'].mean():.1%}")
    st.caption(
        "Predictions cover all stored orders, including the ones the model was trained on, "
        "so they look better here than they would on new orders."
    )

    month = data["order_date"].dt.to_period("M").dt.to_timestamp()
    monthly = data.groupby(month).agg(
        order_items=("order_item_id", "count"),
        late_rate=("late_delivery_risk", "mean"),
    )
    # Some regions have months with no orders at all; list them explicitly so the charts show the gap
    # (0 order items, blank late rate) instead of drawing a straight line across it.
    all_months = pd.date_range(monthly.index.min(), monthly.index.max(), freq="MS")
    monthly = monthly.reindex(all_months)
    monthly["order_items"] = monthly["order_items"].fillna(0)
    left, right = st.columns(2)
    left.subheader("Order items per month")
    left.line_chart(monthly["order_items"])
    right.subheader("Actual late rate per month (%)")
    right.line_chart(monthly["late_rate"] * 100)

    st.subheader("Actual late rate vs average predicted risk by shipping mode (%)")
    by_mode = data.groupby("shipping_mode").agg(
        actual_late_rate=("late_delivery_risk", "mean"),
        predicted_risk=("risk_probability", "mean"),
    )
    st.bar_chart(by_mode * 100, stack=False)

    st.subheader(f"Top {TOP_ORDERS} highest-risk order items")
    top = data.nlargest(TOP_ORDERS, "risk_probability")
    table = top[["order_item_id", "order_date", "order_region", "order_country", "shipping_mode", "product_name"]].copy()
    table["risk (%)"] = (top["risk_probability"] * 100).round(1)
    table["actually late"] = top["late_delivery_risk"].map({1: "Yes", 0: "No"})
    st.dataframe(table, hide_index=True)


# ---------- single-order risk checker ----------

def pick(container, label, rows, column):
    """Select box with the values of `column` that appear in `rows`."""
    return container.selectbox(label, sorted(rows[column].unique()))


def show_checker(user, model):
    st.header("Order risk checker")
    st.write("Describe a new order. Each list only offers values that fit the choices above it.")
    orders = load_orders_for(user["role"], user["region"])
    left, middle, right = st.columns(3)

    left.subheader("Destination")
    order_region = pick(left, "Order region", orders, "order_region")
    in_region = orders[orders["order_region"] == order_region]
    order_country = pick(left, "Order country", in_region, "order_country")
    in_country = in_region[in_region["order_country"] == order_country]
    order_state = pick(left, "Order state", in_country, "order_state")
    order_city = pick(left, "Order city", in_country[in_country["order_state"] == order_state], "order_city")
    market = in_region["market"].iloc[0]  # each region belongs to exactly one market
    left.write(f"Market: **{market}**")

    middle.subheader("Customer and product")
    customer_segment = pick(middle, "Customer segment", orders, "customer_segment")
    customer_country = pick(middle, "Customer country", orders, "customer_country")
    in_customer_country = orders[orders["customer_country"] == customer_country]
    customer_state = pick(middle, "Customer state", in_customer_country, "customer_state")
    customer_city = pick(
        middle, "Customer city",
        in_customer_country[in_customer_country["customer_state"] == customer_state], "customer_city",
    )
    department_name = pick(middle, "Department", orders, "department_name")
    in_department = orders[orders["department_name"] == department_name]
    category_name = pick(middle, "Category", in_department, "category_name")
    in_category = in_department[in_department["category_name"] == category_name]
    product_name = pick(middle, "Product", in_category, "product_name")

    right.subheader("Order details")
    order_date = right.date_input("Order date", value=date.today())
    payment_type = pick(right, "Payment type", orders, "payment_type")
    shipping_mode = pick(right, "Shipping mode", orders, "shipping_mode")
    usual_price = float(in_category.loc[in_category["product_name"] == product_name, "product_price"].median())
    product_price = right.number_input("Product price", min_value=0.0, value=usual_price, step=1.0)
    quantity = right.number_input("Quantity", min_value=1, max_value=100, value=1, step=1)
    discount_rate = right.number_input("Discount rate (0 to 1)", min_value=0.0, max_value=1.0, value=0.0, step=0.01)

    if not st.button("Check risk", type="primary"):
        return

    order = pd.DataFrame([{
        "payment_type": payment_type, "shipping_mode": shipping_mode,
        "customer_segment": customer_segment, "customer_country": customer_country,
        "customer_state": customer_state, "customer_city": customer_city,
        "market": market, "order_region": order_region, "order_country": order_country,
        "order_state": order_state, "order_city": order_city,
        "category_name": category_name, "department_name": department_name, "product_name": product_name,
        "product_price": float(product_price), "quantity": int(quantity), "discount_rate": float(discount_rate),
        "order_date": pd.Timestamp(order_date),
    }])
    probabilities, levels = score(model, order)
    pipeline = model.estimator_.estimator  # FixedThresholdClassifier(FrozenEstimator(pipeline))
    background = load_background()
    average_risk = pipeline.predict_proba(background)[:, 1].mean()

    col1, col2 = st.columns(2)
    col1.metric("Probability of late delivery", f"{probabilities[0]:.1%}")
    col2.metric("Risk level", levels[0])
    st.write(f"The average order in the SHAP background sample has {average_risk:.1%} risk.")

    # A fresh explainer for every request: shap seeds its random orderings once, in the constructor,
    # so only a new explainer gives the same explanation for the same order every time (builds in ~0.02 s).
    with st.spinner("Explaining the prediction (a few seconds)..."):
        explainer = build_explainer(pipeline, background)
        reasons = explain_order(order, pipeline, explainer, top_n=5)
    st.subheader("Top factors")
    for reason in reasons:
        st.write(f"- {reason}")


# ---------- batch CSV scoring ----------

def validate_upload(df, role, region):
    """Check and convert an uploaded file. Returns (clean rows, []) or (None, list of error messages)."""
    missing = [column for column in MODEL_INPUTS if column not in df.columns]
    if missing:
        return None, [f"Missing columns: {', '.join(missing)}"]
    if df.empty:
        return None, ["The file has no rows."]

    # Drop the actual outcome if it is present, so it can never reach the model.
    clean = df.drop(columns=[TARGET], errors="ignore").copy()
    clean["order_date"] = pd.to_datetime(clean["order_date"], errors="coerce")
    for column in NUMERIC_FEATURES:
        # "inf" parses as a number, so infinite values are turned into missing ones and reported below.
        clean[column] = pd.to_numeric(clean[column], errors="coerce").replace([np.inf, -np.inf], np.nan)
    for column in CATEGORICAL_FEATURES:
        text = clean[column].astype("string").str.strip()
        clean[column] = text.mask(text == "")

    errors = []
    invalid = clean[MODEL_INPUTS].isna().sum()
    for column, count in invalid[invalid > 0].items():
        errors.append(f"{column}: {count} missing or invalid values")
    if (clean["quantity"] < 1).any() or (clean["quantity"] % 1 != 0).any():
        errors.append("quantity: must be a whole number of at least 1")
    if (clean["product_price"] < 0).any():
        errors.append("product_price: must not be negative")
    if ((clean["discount_rate"] < 0) | (clean["discount_rate"] > 1)).any():
        errors.append("discount_rate: must be between 0 and 1")
    if role != "admin":
        outside = (clean["order_region"] != region).sum()
        if outside:
            errors.append(f"order_region: {outside} rows are outside your region ({region})")
    if errors:
        return None, errors

    clean[CATEGORICAL_FEATURES] = clean[CATEGORICAL_FEATURES].astype(str)
    clean["quantity"] = clean["quantity"].astype(int)
    return clean, []


def show_batch(user, model):
    st.header("Batch scoring")
    st.write(f"Upload a CSV with these columns (others are kept but not used): {', '.join(MODEL_INPUTS)}")
    uploaded = st.file_uploader("Orders CSV", type="csv")
    if uploaded is None:
        return

    try:
        df = pd.read_csv(uploaded)
    except (pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeDecodeError) as error:
        st.error(f"Could not read the file: {error}")
        return

    clean, errors = validate_upload(df, user["role"], user["region"])
    if errors:
        st.error("The file was not scored:\n\n" + "\n".join(f"- {message}" for message in errors))
        return

    clean["risk_probability"], clean["risk_level"] = score(model, clean)
    clean = clean.sort_values("risk_probability", ascending=False)
    high = (clean["risk_level"] == HIGH).sum()
    st.success(f"Scored {len(clean):,} rows: {high:,} high risk, {len(clean) - high:,} low risk.")
    st.dataframe(clean, hide_index=True)
    st.download_button(
        "Download results (CSV)", clean.to_csv(index=False), file_name="risk_scores.csv", mime="text/csv"
    )


# ---------- main ----------

def main():
    # The checker also needs the processed CSV (SHAP background), so all three files are checked here.
    missing = [str(path) for path in (PROCESSED_FILE, MODEL_FILE, db.DB_FILE) if not path.exists()]
    if missing:
        st.error(
            f"Missing: {', '.join(missing)}. From the project root run, in order: "
            "`.venv/bin/python -m src.data_prep`, `.venv/bin/python -m src.train`, "
            "`.venv/bin/python -m src.db` (see docs/setup.md)."
        )
        st.stop()

    if "user" not in st.session_state:
        show_login()
        return

    user = st.session_state["user"]
    model = load_model()
    ensure_predictions(model)

    with st.sidebar:
        st.write(f"Logged in as **{user['username']}** ({user['role']})")
        st.write("Regions: " + ("all" if user["role"] == "admin" else user["region"]))
        page = st.radio("Page", ["Dashboard", "Order risk checker", "Batch scoring"])
        if st.button("Log out"):
            del st.session_state["user"]
            st.rerun()

    if page == "Dashboard":
        show_dashboard(user)
    elif page == "Order risk checker":
        show_checker(user, model)
    else:
        show_batch(user, model)


main()
````
