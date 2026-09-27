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
