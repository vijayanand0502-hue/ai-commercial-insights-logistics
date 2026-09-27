# Data Dictionary

| Item | Value |
|---|---|
| Dataset | DataCo Smart Supply Chain (Kaggle) |
| Source file | `data/raw/DataCoSupplyChainDataset.csv` |
| Encoding | cp1252 (Windows-1252) |
| Raw size | 180,519 rows x 53 columns |
| Row filter | Orders with `Order Status` = `CANCELED` or `SUSPECTED_FRAUD` removed (never shipped, so the label is meaningless); 3 rows whose `Customer State` is a zip code (`95758`, `91732`) removed as shifted rows |
| Clean size | 172,762 rows x 22 columns, 0 missing values |
| Clean file | `data/processed/orders_clean.csv` (UTF-8), produced by `src/data_prep.py` |
| Other cleaning | Leading/trailing spaces stripped from text columns; `order_date` parsed with format `%m/%d/%Y %H:%M`; script stops with an error if any value is missing (0 expected) |

Status counts (all 53 raw columns):

| Status | Count |
|---|---|
| Feature | 19 |
| Target | 1 |
| Key (not a feature) | 2 |
| Excluded - leakage | 4 |
| Excluded - leakage (uncertain timing) | 3 |
| Dropped - personal data | 8 |
| Dropped - redundant ID | 7 |
| Dropped - duplicate | 5 |
| Dropped - no information | 4 |
| **Total** | **53** |

Kept in clean file: 19 + 1 + 2 = 22 columns.

## Column table

Type uses Numeric / Alpha / Date / Binary, with the raw pandas dtype in brackets. Range, uniques and % missing are computed on the full raw file (180,519 rows), before the row filter.

| # | Raw column | Clean name | Type | Range / max length | % missing | Status | Notes |
|---|---|---|---|---|---|---|---|
| 1 | Type | payment_type | Alpha (text) | max len 8; 4 unique | 0.0 | Feature | Payment type |
| 2 | Days for shipping (real) | — | Numeric (int64) | 0 to 6; 7 unique | 0.0 | Excluded - leakage | Actual shipping days; known only after delivery |
| 3 | Days for shipment (scheduled) | scheduled_shipping_days | Numeric (int64) | 0 to 4; 4 unique | 0.0 | Feature | Planned shipping days |
| 4 | Benefit per order | — | Numeric (float64) | -4274.98 to 911.80; 21,998 unique | 0.0 | Excluded - leakage (uncertain timing) | Profit; may include costs known only after delivery |
| 5 | Sales per customer | — | Numeric (float64) | 7.49 to 1939.99; 2,927 unique | 0.0 | Dropped - duplicate | Same as Order Item Total (itself dropped) |
| 6 | Delivery Status | — | Alpha (text) | max len 17; 4 unique | 0.0 | Excluded - leakage | Delivery outcome; recorded after delivery |
| 7 | Late_delivery_risk | late_delivery_risk | Binary (int64) | 0 to 1; 2 unique | 0.0 | Target | 1 = late, 0 = on time |
| 8 | Category Id | — | Numeric (int64) | 2 to 76; 51 unique | 0.0 | Dropped - redundant ID | Code for Category Name |
| 9 | Category Name | category_name | Alpha (text) | max len 20; 50 unique | 0.0 | Feature | Product category |
| 10 | Customer City | customer_city | Alpha (text) | max len 20; 563 unique | 0.0 | Feature | Customer city |
| 11 | Customer Country | customer_country | Alpha (text) | max len 11; 2 unique | 0.0 | Feature | Customer country |
| 12 | Customer Email | — | Alpha (text) | max len 9; 1 unique | 0.0 | Dropped - personal data | Already masked in source |
| 13 | Customer Fname | — | Alpha (text) | max len 11; 782 unique | 0.0 | Dropped - personal data | Customer first name |
| 14 | Customer Id | — | Numeric (int64) | 1 to 20757; 20,652 unique | 0.0 | Dropped - redundant ID | Customer code |
| 15 | Customer Lname | — | Alpha (text) | max len 12; 1,109 unique | 0.0 | Dropped - personal data | Customer last name |
| 16 | Customer Password | — | Alpha (text) | max len 9; 1 unique | 0.0 | Dropped - personal data | Already masked in source |
| 17 | Customer Segment | customer_segment | Alpha (text) | max len 11; 3 unique | 0.0 | Feature | Customer segment |
| 18 | Customer State | customer_state | Alpha (text) | max len 5; 46 unique | 0.0 | Feature | Customer state |
| 19 | Customer Street | — | Alpha (text) | max len 33; 7,458 unique | 0.0 | Dropped - personal data | Street address |
| 20 | Customer Zipcode | — | Numeric (float64) | 603 to 99205; 995 unique | 0.0 | Dropped - personal data | Precise location; city/state already kept |
| 21 | Department Id | — | Numeric (int64) | 2 to 12; 11 unique | 0.0 | Dropped - redundant ID | Code for Department Name |
| 22 | Department Name | department_name | Alpha (text) | max len 18; 11 unique | 0.0 | Feature | Product department |
| 23 | Latitude | — | Numeric (float64) | -33.94 to 48.78; 11,250 unique | 0.0 | Dropped - personal data | Precise location |
| 24 | Longitude | — | Numeric (float64) | -158.03 to 115.26; 4,487 unique | 0.0 | Dropped - personal data | Precise location |
| 25 | Market | market | Alpha (text) | max len 12; 5 unique | 0.0 | Feature | Market |
| 26 | Order City | order_city | Alpha (text) | max len 35; 3,597 unique | 0.0 | Feature | Order destination city |
| 27 | Order Country | order_country | Alpha (text) | max len 31; 164 unique | 0.0 | Feature | Order destination country |
| 28 | Order Customer Id | — | Numeric (int64) | 1 to 20757; 20,652 unique | 0.0 | Dropped - redundant ID | Duplicate of Customer Id |
| 29 | order date (DateOrders) | order_date | Date (text, parsed to datetime) | max len 16; 65,752 unique; format m/d/YYYY H:MM | 0.0 | Feature | Order placement date and time |
| 30 | Order Id | order_id | Numeric (int64) | 1 to 77204; 65,752 unique | 0.0 | Key (not a feature) | Database key and split group |
| 31 | Order Item Cardprod Id | — | Numeric (int64) | 19 to 1363; 118 unique | 0.0 | Dropped - redundant ID | Product code |
| 32 | Order Item Discount | — | Numeric (float64) | 0.0 to 500.0; 1,017 unique | 0.0 | Dropped - duplicate | Equals price x quantity x discount rate |
| 33 | Order Item Discount Rate | discount_rate | Numeric (float64) | 0.0 to 0.25; 18 unique | 0.0 | Feature | Discount rate |
| 34 | Order Item Id | order_item_id | Numeric (int64) | 1 to 180519; 180,519 unique | 0.0 | Key (not a feature) | Database key (one row per order item) |
| 35 | Order Item Product Price | product_price | Numeric (float64) | 9.99 to 1999.99; 75 unique | 0.0 | Feature | Unit product price |
| 36 | Order Item Profit Ratio | — | Numeric (float64) | -2.75 to 0.5; 162 unique | 0.0 | Excluded - leakage (uncertain timing) | Profit ratio; may include costs known only after delivery |
| 37 | Order Item Quantity | quantity | Numeric (int64) | 1 to 5; 5 unique | 0.0 | Feature | Quantity ordered |
| 38 | Sales | — | Numeric (float64) | 9.99 to 1999.99; 193 unique | 0.0 | Dropped - duplicate | Equals price x quantity |
| 39 | Order Item Total | — | Numeric (float64) | 7.49 to 1939.99; 2,927 unique | 0.0 | Dropped - duplicate | Equals price x quantity - discount |
| 40 | Order Profit Per Order | — | Numeric (float64) | -4274.98 to 911.80; 21,998 unique | 0.0 | Excluded - leakage (uncertain timing) | Duplicate of Benefit per order; profit timing uncertain |
| 41 | Order Region | order_region | Alpha (text) | max len 15; 23 unique | 0.0 | Feature | Order destination region |
| 42 | Order State | order_state | Alpha (text) | max len 36; 1,089 unique | 0.0 | Feature | Order destination state |
| 43 | Order Status | — | Alpha (text) | max len 15; 9 unique | 0.0 | Excluded - leakage | Order status; used for the row filter, then dropped |
| 44 | Order Zipcode | — | Numeric (float64) | 1040 to 99301; 609 unique | 86.2 | Dropped - no information | Mostly missing |
| 45 | Product Card Id | — | Numeric (int64) | 19 to 1363; 118 unique | 0.0 | Dropped - redundant ID | Product code |
| 46 | Product Category Id | — | Numeric (int64) | 2 to 76; 51 unique | 0.0 | Dropped - redundant ID | Duplicate of Category Id |
| 47 | Product Description | — | Numeric (float64) | all NaN | 100.0 | Dropped - no information | Empty column |
| 48 | Product Image | — | Alpha (text, URL) | max len 94; 118 unique | 0.0 | Dropped - no information | Image URL |
| 49 | Product Name | product_name | Alpha (text) | max len 45; 118 unique | 0.0 | Feature | Product name |
| 50 | Product Price | — | Numeric (float64) | 9.99 to 1999.99; 75 unique | 0.0 | Dropped - duplicate | Same as Order Item Product Price |
| 51 | Product Status | — | Numeric (int64) | 0 to 0; 1 unique | 0.0 | Dropped - no information | Constant (always 0) |
| 52 | shipping date (DateOrders) | — | Date (text) | max len 16; 63,701 unique | 0.0 | Excluded - leakage | Shipping date; known only after shipping |
| 53 | Shipping Mode | shipping_mode | Alpha (text) | max len 14; 4 unique | 0.0 | Feature | Shipping mode |

## Status labels

- **Feature**: kept in the clean file and available as a model input (known when the order is placed).
- **Target**: the label the model predicts.
- **Key (not a feature)**: kept for database joins and grouping; never a model input.
- **Excluded - leakage**: recorded after shipping or delivery (`LEAKAGE_COLUMNS` in `src/data_prep.py`).
- **Excluded - leakage (uncertain timing)**: profit columns that may include costs known only after delivery (`UNCERTAIN_TIMING_COLUMNS`).
- **Dropped - personal data**: personal data or precise location (`PERSONAL_COLUMNS`).
- **Dropped - redundant ID**: numeric code duplicating a name column or another ID (`IDENTIFIER_COLUMNS`).
- **Dropped - duplicate**: exact copy or formula of other columns (price, quantity, discount rate) (`DUPLICATE_COLUMNS`).
- **Dropped - no information**: empty, mostly empty, constant, or a URL (`NO_INFORMATION_COLUMNS`).
