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
from src.data_prep import load_processed
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
    if not db.DB_FILE.exists() or not MODEL_FILE.exists():
        st.error("Database or model missing. Run: python -m src.db and python -m src.train (see docs/setup.md).")
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
