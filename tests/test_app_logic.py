"""Tests for app.py: upload validation, scoring and role-based access.

app.py is a Streamlit script, so importing it runs main() in "bare mode" (it shows the
login form and returns; Streamlit prints harmless "missing ScriptRunContext" warnings).

The access-control tests drive the real app with streamlit.testing.v1.AppTest and log in
with the demo users. The app runs on a private COPY of data/app.db (it may save predictions
there at the first login), so the real data/app.db is never changed by these tests.

Skipped if data/app.db or models/model.joblib is missing.
"""

import shutil
import sqlite3
from pathlib import Path

import joblib
import pandas as pd
import pytest

from src import db
from src.train import MODEL_FILE

if not db.DB_FILE.exists() or not MODEL_FILE.exists():
    pytest.skip("data/app.db or models/model.joblib missing", allow_module_level=True)

import app  # noqa: E402  (must come after the skip check)

APP_FILE = Path(__file__).resolve().parent.parent / "app.py"
ANALYST_REGION = "Central America"


def make_upload(n=3, region=ANALYST_REGION):
    """A small upload in the clean-CSV format (as read from a CSV: dates and numbers are text)."""
    return pd.DataFrame({
        "payment_type": ["DEBIT"] * n,
        "shipping_mode": ["Standard Class"] * n,
        "customer_segment": ["Consumer"] * n,
        "customer_country": ["Puerto Rico"] * n,
        "customer_state": ["PR"] * n,
        "customer_city": ["Caguas"] * n,
        "market": ["LATAM"] * n,
        "order_region": [region] * n,
        "order_country": ["Mexico"] * n,
        "order_state": ["Jalisco"] * n,
        "order_city": ["Guadalajara"] * n,
        "category_name": ["Cleats"] * n,
        "department_name": ["Apparel"] * n,
        "product_name": ["Perfect Fitness Perfect Rip Deck"] * n,
        "product_price": ["59.99"] * n,
        "quantity": ["1"] * n,
        "discount_rate": ["0.05"] * n,
        "order_date": ["2018-01-31 22:56:00"] * n,
        "late_delivery_risk": [1] * n,  # the real outcome; must be dropped
    })


def validate_as_analyst(df):
    return app.validate_upload(df, "analyst", ANALYST_REGION)


# ---------- validate_upload: valid files ----------

def test_valid_upload_passes_and_drops_target():
    clean, errors = validate_as_analyst(make_upload())
    assert errors == []
    assert len(clean) == 3
    assert "late_delivery_risk" not in clean.columns
    assert pd.api.types.is_datetime64_any_dtype(clean["order_date"])
    assert clean["quantity"].tolist() == [1, 1, 1]
    assert clean["product_price"].tolist() == [59.99, 59.99, 59.99]  # text converted to numbers


def test_valid_upload_keeps_extra_columns():
    df = make_upload()
    df["my_note"] = "keep me"
    clean, errors = validate_as_analyst(df)
    assert errors == []
    assert list(clean["my_note"]) == ["keep me"] * 3


def test_valid_upload_strips_spaces_in_text():
    df = make_upload()
    df["order_region"] = "  Central America  "
    clean, errors = validate_as_analyst(df)
    assert errors == []
    assert set(clean["order_region"]) == {ANALYST_REGION}


# ---------- validate_upload: rejected files ----------

def test_missing_columns_rejected():
    df = make_upload().drop(columns=["shipping_mode", "order_date"])
    clean, errors = validate_as_analyst(df)
    assert clean is None
    assert errors == ["Missing columns: shipping_mode, order_date"]


def test_wrong_column_names_rejected():
    df = make_upload().rename(columns={"quantity": "qty"})
    clean, errors = validate_as_analyst(df)
    assert clean is None
    assert "quantity" in errors[0]


def test_empty_file_rejected():
    clean, errors = validate_as_analyst(make_upload().iloc[0:0])
    assert clean is None
    assert errors == ["The file has no rows."]


@pytest.mark.filterwarnings("ignore:Could not infer format")
def test_bad_date_rejected():
    df = make_upload()
    df.loc[0, "order_date"] = "not a date"
    clean, errors = validate_as_analyst(df)
    assert clean is None
    assert "order_date: 1 missing or invalid values" in errors


def test_non_numeric_price_rejected():
    df = make_upload()
    df.loc[1, "product_price"] = "cheap"
    clean, errors = validate_as_analyst(df)
    assert clean is None
    assert "product_price: 1 missing or invalid values" in errors


def test_negative_price_rejected():
    df = make_upload()
    df.loc[0, "product_price"] = "-5"
    clean, errors = validate_as_analyst(df)
    assert clean is None
    assert "product_price: must not be negative" in errors


def test_blank_text_rejected():
    df = make_upload()
    df.loc[2, "customer_city"] = "   "
    clean, errors = validate_as_analyst(df)
    assert clean is None
    assert "customer_city: 1 missing or invalid values" in errors


@pytest.mark.parametrize("bad_quantity", ["0", "2.5"])
def test_quantity_not_whole_number_of_at_least_1_rejected(bad_quantity):
    df = make_upload()
    df.loc[0, "quantity"] = bad_quantity
    clean, errors = validate_as_analyst(df)
    assert clean is None
    assert "quantity: must be a whole number of at least 1" in errors


@pytest.mark.parametrize("bad_discount", ["-0.1", "1.5"])
def test_discount_outside_0_1_rejected(bad_discount):
    df = make_upload()
    df.loc[0, "discount_rate"] = bad_discount
    clean, errors = validate_as_analyst(df)
    assert clean is None
    assert "discount_rate: must be between 0 and 1" in errors


def test_infinite_price_rejected():
    # Was known issue KI-1: "inf" parses as a number and used to be accepted and scored.
    df = make_upload()
    df.loc[0, "product_price"] = "inf"
    clean, errors = validate_as_analyst(df)
    assert clean is None
    assert "product_price: 1 missing or invalid values" in errors


# ---------- validate_upload: region access ----------

def test_analyst_upload_with_other_region_rejected():
    df = make_upload()
    df.loc[0, "order_region"] = "Western Europe"
    clean, errors = validate_as_analyst(df)
    assert clean is None
    assert errors == [f"order_region: 1 rows are outside your region ({ANALYST_REGION})"]


def test_admin_upload_with_many_regions_accepted():
    df = make_upload()
    df.loc[0, "order_region"] = "Western Europe"
    df.loc[1, "order_region"] = "South Asia"
    clean, errors = app.validate_upload(df, "admin", db.ALL_REGIONS)
    assert errors == []
    assert len(clean) == 3


# ---------- score ----------

@pytest.fixture(scope="module")
def model():
    return joblib.load(MODEL_FILE)


def test_score_returns_probabilities_between_0_and_1(model):
    clean, _ = validate_as_analyst(make_upload())
    probabilities, levels = app.score(model, clean)
    assert len(probabilities) == len(levels) == 3
    assert ((probabilities >= 0) & (probabilities <= 1)).all()


def test_score_levels_match_model_predict_and_threshold(model):
    clean, _ = app.validate_upload(pd.read_csv(db.PROCESSED_FILE, nrows=50), "admin", db.ALL_REGIONS)
    probabilities, levels = app.score(model, clean)
    predicted = model.predict(clean[app.MODEL_INPUTS])
    assert levels == ["High" if p == 1 else "Low" for p in predicted]
    assert levels == ["High" if p >= model.threshold else "Low" for p in probabilities]
    assert set(levels) <= {"High", "Low"}


def test_score_without_a_model_input_raises(model):
    clean, _ = validate_as_analyst(make_upload())
    with pytest.raises(KeyError):
        app.score(model, clean.drop(columns=["shipping_mode"]))


# ---------- access control through the real app (AppTest) ----------

from streamlit.delta_generator_singletons import context_dg_stack  # noqa: E402
from streamlit.testing.v1 import AppTest  # noqa: E402


def clear_bare_mode_form():
    """Importing app.py above (bare mode) leaves Streamlit's shared page container marked as
    "inside the login form". That is a Streamlit bare-mode side effect, not an app bug, but it
    makes AppTest fail with "Forms cannot be nested". Clearing the mark gives AppTest a clean page."""
    # _form_data is a private Streamlit API: this only works with the pinned streamlit version (1.64.0).
    for container in context_dg_stack.get():
        container._form_data = None


def read_only_connection(path=db.DB_FILE):
    """Open data/app.db read-only, so no test can write to it."""
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@pytest.fixture(scope="module")
def app_db_copy(tmp_path_factory):
    """A private copy of data/app.db. The app may write to it (after a fresh build it saves
    predictions at the first login), while the real data/app.db is never changed."""
    path = tmp_path_factory.mktemp("app_db") / "app.db"
    shutil.copy(db.DB_FILE, path)
    return path


@pytest.fixture
def running_app(monkeypatch, app_db_copy):
    """The app at its login screen, using the private copy of the database."""
    clear_bare_mode_form()
    real_get_connection = db.get_connection  # keeps the foreign-key setting
    monkeypatch.setattr(db, "get_connection", lambda path=None: real_get_connection(app_db_copy))
    return AppTest.from_file(str(APP_FILE), default_timeout=120).run()


def log_in(app_test, username, password):
    app_test.text_input[0].input(username)
    app_test.text_input[1].input(password)
    app_test.button[0].click().run()
    return app_test


def log_in_or_skip(app_test, username, password):
    log_in(app_test, username, password)
    if "user" not in app_test.session_state:
        pytest.skip(f"'{username}' could not log in with the default password (env-var passwords used?)")
    return app_test


def test_wrong_password_shows_error_and_stays_logged_out(running_app):
    log_in(running_app, "analyst", "wrong-password")
    assert [e.value for e in running_app.error] == ["Wrong username or password."]
    assert "user" not in running_app.session_state


def test_analyst_dashboard_shows_only_central_america(running_app):
    log_in_or_skip(running_app, "analyst", "analyst123")
    assert not running_app.exception
    markdown = [m.value for m in running_app.markdown]
    assert f"Region: **{ANALYST_REGION}**" in markdown
    assert "Region" not in [s.label for s in running_app.selectbox]  # no region selector
    top_table = running_app.dataframe[0].value
    assert set(top_table["order_region"]) == {ANALYST_REGION}

    # The "Order items" count equals the number of Central America orders in the database.
    conn = read_only_connection()
    expected = conn.execute("SELECT COUNT(*) FROM orders WHERE order_region = ?", (ANALYST_REGION,)).fetchone()[0]
    conn.close()
    order_items = [m.value for m in running_app.metric if m.label == "Order items"][0]
    assert order_items == f"{expected:,}"


def test_analyst_checker_offers_only_own_region(running_app):
    log_in_or_skip(running_app, "analyst", "analyst123")
    running_app.sidebar.radio[0].set_value("Order risk checker").run()
    region_box = [s for s in running_app.selectbox if s.label == "Order region"][0]
    assert region_box.options == [ANALYST_REGION]


def test_admin_sees_region_selector_with_all_regions(running_app):
    log_in_or_skip(running_app, "admin", "admin123")
    assert not running_app.exception
    region_box = [s for s in running_app.selectbox if s.label == "Region"][0]
    assert region_box.options[0] == "All regions"
    assert ANALYST_REGION in region_box.options
    assert len(region_box.options) > 2  # more than one real region
    assert "Regions: all" in [m.value for m in running_app.sidebar.markdown]
