# Test report

Automated tests for the late delivery risk project, first run on 2026-09-28; re-run on 2026-09-30 after fixing KI-1 and KI-2.

## Environment

| Item | Version |
|---|---|
| OS | macOS (Darwin 27.0.0) |
| Python | 3.12.6 (project `.venv`) |
| pandas | 3.0.6 |
| numpy | 2.5.3 |
| scikit-learn | 1.9.1 |
| shap | 0.52.0 |
| streamlit | 1.64.0 |
| pytest | 9.1.1 |

## How to run

From the project root:

```bash
.venv/bin/python -m pytest            # all tests
.venv/bin/python -m pytest -v -rxs    # one line per test, plus reasons for skips and xfails
```

- Tests use small hand-made DataFrames and temporary files and databases (pytest `tmp_path`).
  They never write to `data/app.db`, `data/processed/`, `models/` or `reports/figures/`.
- A few tests use the real built files and are **skipped** if these are missing:
  `data/processed/orders_clean.csv` (DP-19, TR-13, TR-14, all of test_explain),
  `models/model.joblib` (TR-13, TR-14, test_explain, all of test_app_logic) and
  `data/app.db` (all of test_app_logic).
- The access-control tests (AP-21 to AP-24) run the real app with `streamlit.testing.v1.AppTest`
  and log in with the demo users `admin` / `admin123` and `analyst` / `analyst123` (docs/setup.md).
  They run the app on a private **copy** of `data/app.db`, so the real database is never changed (the app may
  save predictions in the copy at the first login after a fresh build). If the demo users were created with
  other passwords (env vars), the login tests are skipped.
- The full training (`python -m src.train`) is not run by the tests because it is too slow.
  Its functions are tested on small synthetic data instead.

## Summary

| Result | Count |
|---|---|
| Passed | 107 |
| Failed | 0 |
| Skipped | 0 |
| **Total** | **107** |
| Runtime | 13.7 s |

pytest summary line: `107 passed, 3 warnings in 13.69s`
(the 3 warnings are PendingDeprecationWarnings from inside the shap library, not from project code).

First run (2026-09-28): `105 passed, 2 xfailed` — the 2 expected failures were known issues KI-1 and KI-2,
fixed on 2026-09-30 (see "Known issues found").

## Test cases

Status: **Pass** = behaved as expected.

### src/data_prep.py (tests/test_data_prep.py)

| Test ID | Module | Test case | Expected result | Actual result | Status |
|---|---|---|---|---|---|
| DP-01 | data_prep | Rows with Order Status CANCELED and SUSPECTED_FRAUD | Removed; COMPLETE and PENDING rows kept | 2 of 4 rows kept (COMPLETE, PENDING) | Pass |
| DP-02 | data_prep | Leakage columns after drop_rows_and_columns | Days for shipping (real), Delivery Status, shipping date (DateOrders), Order Status all absent | All absent | Pass |
| DP-03 | data_prep | Columns left after drop_rows_and_columns | Exactly the approved KEEP_AND_RENAME columns | Exactly the approved columns | Pass |
| DP-04 | data_prep | Raw data without the Order Status column | KeyError | KeyError raised | Pass |
| DP-05 | data_prep | Kept-column list vs dropped-column lists | No column is in both | No overlap | Pass |
| DP-06 | data_prep | strip_text on " Oceania " and a number column | Spaces removed; numbers unchanged | "Oceania"; numbers unchanged | Pass |
| DP-07 | data_prep | strip_text on "  Standard Class  " | Inner space kept; input DataFrame not changed | "Standard Class"; input unchanged | Pass |
| DP-08 | data_prep | rename_columns on the approved columns | snake_case names incl. late_delivery_risk | All 22 snake_case names | Pass |
| DP-09 | data_prep | rename_columns with Delivery Status added back | ValueError "not in the approved list" | ValueError raised | Pass |
| DP-10 | data_prep | rename_columns with Shipping Mode missing | ValueError "missing from the data" | ValueError raised | Pass |
| DP-11 | data_prep | drop_bad_states on PR, 95758, CA, 91732 | Zip-code states dropped | PR and CA kept | Pass |
| DP-12 | data_prep | drop_bad_states with no bad rows | All rows kept | 2 of 2 kept | Pass |
| DP-13 | data_prep | parse_dates on "1/31/2018 22:56", "12/5/2017 7:03" | Correct datetimes | 2018-01-31 22:56, 2017-12-05 07:03 | Pass |
| DP-14 | data_prep | parse_dates input | Input DataFrame not changed | Unchanged | Pass |
| DP-15 | data_prep | parse_dates on "2018-31-01" (wrong format) | ValueError | ValueError raised | Pass |
| DP-16 | data_prep | check_missing on complete data | No error | No error | Pass |
| DP-17 | data_prep | check_missing with one missing value | ValueError "Unexpected missing values" | ValueError raised | Pass |
| DP-18 | data_prep | Whole pipeline on a 3-row raw frame, then save/load in a temp folder | 1 row left (CANCELED and zip-code rows removed); order_date is a datetime after reload | 1 row; datetime | Pass |
| DP-19 | data_prep | Real orders_clean.csv | No leakage columns, only approved columns, no missing values, order_item_id unique, target only 0/1 | All true | Pass |

### src/features.py (tests/test_features.py)

| Test ID | Module | Test case | Expected result | Actual result | Status |
|---|---|---|---|---|---|
| FE-01 | features | add_date_features on 2018-01-01, 2017-12-31, 2018-07-04 | month 1/12/7, weekday 0/6/2 (0 = Monday), quarter 1/4/3 | As expected | Pass |
| FE-02 | features | add_date_features input | Input DataFrame not changed | Unchanged | Pass |
| FE-03 | features | add_date_features on text dates | AttributeError (dates must be parsed first) | AttributeError raised | Pass |
| FE-04 | features | Leakage check: feature lists vs leakage, target, ID, order_date and scheduled_shipping_days | None of them used as a feature | None used | Pass |
| FE-05 | features | Every feature comes from the approved columns or is a date part | True | True | Pass |
| FE-06 | features | Feature list size and duplicates | 17 categorical (14 + 3 date parts), 3 numeric, no duplicates | As expected | Pass |
| FE-07 | features | Logistic preprocessor, unseen shipping_mode "Drone" | No error, no NaN in output | No error, no NaN | Pass |
| FE-08 | features | Tree preprocessor, unseen shipping_mode "Drone" | Coded as -1; seen modes coded 0 and 1 | -1; seen modes 0 and 1 | Pass |
| FE-09 | features | Tree preprocessor output columns | One column per feature; IDs, target, order_date, scheduled_shipping_days dropped | As expected | Pass |
| FE-10 | features | build_preprocessor("forest") | ValueError | ValueError raised | Pass |

### src/train.py (tests/test_train.py)

| Test ID | Module | Test case | Expected result | Actual result | Status |
|---|---|---|---|---|---|
| TR-01 | train | split_train_test on 100 orders with 1 to 3 items each | No order_id on both sides; no rows lost | Disjoint; all rows kept | Pass |
| TR-02 | train | Test-set share | About 20% (15 to 25%) | Within range | Pass |
| TR-03 | train | split_train_test with only 4 orders | ValueError (5 folds need 5 groups) | ValueError raised | Pass |
| TR-04 | train | choose_threshold on synthetic data (logistic regression, 3 grouped folds) | Threshold in (0, 1) with out-of-fold recall >= TARGET_RECALL (0.80) | As expected | Pass |
| TR-05 | train | choose_threshold picks the highest threshold that meets the target | Next higher threshold has recall < 0.80 | As expected | Pass |
| TR-06 | train | choose_threshold with no late items | ValueError | ValueError raised (from the model fit on one class) | Pass |
| TR-07 | train | evaluate returns metrics | Keys accuracy, precision, recall, f1, roc_auc; values in [0, 1] | As expected | Pass |
| TR-08 | train | evaluate on perfectly separable data | accuracy, recall, ROC-AUC = 1.0 | 1.0 | Pass |
| TR-09 | train | evaluate on a test set with one class only | ROC-AUC is NaN (scikit-learn 1.9 warns instead of raising) | NaN | Pass |
| TR-10 | train | Majority baseline with late as the majority | Predicts late (1) for every row | All 1 | Pass |
| TR-11 | train | Shipping-mode baseline | Learns late rate per mode; other columns ignored | First Class -> 1, Standard Class -> 0 | Pass |
| TR-12 | train | Shipping-mode baseline with an unseen mode | No error; probability in [0, 1] | As expected | Pass |
| TR-13 | train | Saved model threshold | About 0.397 | 0.397 | Pass |
| TR-14 | train | Saved model on 20 real rows using only the 18 app input columns | Predictions 0/1; probabilities in [0, 1]; predict agrees with probability >= threshold | As expected | Pass |

### src/db.py (tests/test_db.py)

| Test ID | Module | Test case | Expected result | Actual result | Status |
|---|---|---|---|---|---|
| DB-01 | db | init_db | users, orders, predictions tables exist | Exist | Pass |
| DB-02 | db | init_db run twice | No error, tables kept | As expected | Pass |
| DB-03 | db | hash_password format | "salt$hash", 32-character hex salt, password not in text | As expected | Pass |
| DB-04 | db | Same password hashed twice | Different hashes (random salt) | Different | Pass |
| DB-05 | db | check_password with correct password | True | True | Pass |
| DB-06 | db | check_password with wrong password | False | False | Pass |
| DB-07 | db | verify_user with correct login | Returns username, role, region | As expected | Pass |
| DB-08 | db | Password stored in users table | Not plain text | Only the hash is stored | Pass |
| DB-09 | db | verify_user with wrong password | None | None | Pass |
| DB-10 | db | verify_user with unknown user | None | None | Pass |
| DB-11 | db | verify_user with SQL injection username | None | None | Pass |
| DB-12 | db | add_user with a duplicate username | IntegrityError | IntegrityError raised | Pass |
| DB-13 | db | add_user with role "superuser" | IntegrityError | IntegrityError raised | Pass |
| DB-14 | db | load_orders from a 6-row CSV | Returns 6 | 6 | Pass |
| DB-15 | db | get_orders as admin | All 6 orders | 6 | Pass |
| DB-16 | db | get_orders as analyst (South Asia) | Only South Asia rows | 2 South Asia rows | Pass |
| DB-17 | db | get_orders as analyst with region "All" | No rows (access is by role) | 0 rows | Pass |
| DB-18 | db | get_orders order_date type | datetime | datetime | Pass |
| DB-19 | db | load_orders run again | Predictions cleared, orders not doubled | As expected | Pass |
| DB-20 | db | get_predictions as admin | All 6 predictions | 6 | Pass |
| DB-21 | db | get_predictions as analyst (Central America) | Only own region | 3 Central America rows | Pass |
| DB-22 | db | get_predictions as analyst with region "All" | No rows | 0 rows | Pass |
| DB-23 | db | save_prediction for an unknown order_item_id | IntegrityError (foreign key) | IntegrityError raised | Pass |
| DB-24 | db | save_prediction with probability -0.1 | IntegrityError (CHECK) | IntegrityError raised | Pass |
| DB-25 | db | save_prediction with probability 1.5 | IntegrityError (CHECK) | IntegrityError raised | Pass |
| DB-26 | db | Demo users without env vars | Warning printed; defaults admin123 / analyst123 work | As expected | Pass |
| DB-27 | db | Demo users with env vars | Env passwords work, defaults do not, no warning | As expected | Pass |
| DB-28 | db | create_demo_users run twice | Still 2 users | 2 | Pass |
| DB-29 | db | count_predictions on an empty table | 0 | 0 | Pass |
| DB-30 | db | save_predictions with 3 rows | 3 rows saved with the right ids and levels, one shared timestamp | As expected | Pass |
| DB-31 | db | save_predictions with a pandas Series and a numpy array (as the app passes them) | Saved | 2 rows saved | Pass |
| DB-32 | db | save_predictions with an empty batch | Nothing saved, no error | 0 rows | Pass |
| DB-33 | db | count_predictions after one single save and one bulk save of 2 | 3 | 3 | Pass |
| DB-34 | db | save_predictions batch containing an unknown order_item_id | IntegrityError; nothing committed (checked from a second connection) | IntegrityError; 0 rows committed | Pass |
| DB-35 | db | After a failed batch, another save on the same connection | Only the new row is stored | 1 row stored (first run: 2 rows, the half batch was committed too; fixed, see KI-2) | Pass |
| DB-36 | db | save_predictions with probability -0.1 | IntegrityError (CHECK) | IntegrityError raised | Pass |
| DB-37 | db | save_predictions with probability 1.5 | IntegrityError (CHECK) | IntegrityError raised | Pass |

### src/explain.py (tests/test_explain.py)

| Test ID | Module | Test case | Expected result | Actual result | Status |
|---|---|---|---|---|---|
| EX-01 | explain | explain_order on one real order | 1 to 5 text reasons in "percentage points" | As expected | Pass |
| EX-02 | explain | Two fresh explainers on the same order | Identical reasons | Identical | Pass |
| EX-03 | explain | explain_order with 2 rows | ValueError | ValueError raised | Pass |

### app.py (tests/test_app_logic.py)

| Test ID | Module | Test case | Expected result | Actual result | Status |
|---|---|---|---|---|---|
| AP-01 | app | validate_upload on a valid 3-row file (numbers and dates as text) | Accepted; late_delivery_risk dropped; order_date datetime; quantity int; price numeric | As expected | Pass |
| AP-02 | app | Valid file with an extra column | Accepted; extra column kept | Kept | Pass |
| AP-03 | app | Text with leading/trailing spaces | Accepted; spaces stripped | Stripped | Pass |
| AP-04 | app | shipping_mode and order_date columns missing | Rejected: "Missing columns: shipping_mode, order_date" | As expected | Pass |
| AP-05 | app | quantity column renamed to qty (wrong column name) | Rejected; message names quantity | As expected | Pass |
| AP-06 | app | File with columns but no rows | Rejected: "The file has no rows." | As expected | Pass |
| AP-07 | app | order_date "not a date" | Rejected: "order_date: 1 missing or invalid values" | As expected | Pass |
| AP-08 | app | product_price "cheap" | Rejected: "product_price: 1 missing or invalid values" | As expected | Pass |
| AP-09 | app | product_price -5 | Rejected: "must not be negative" | As expected | Pass |
| AP-10 | app | customer_city of only spaces | Rejected: "customer_city: 1 missing or invalid values" | As expected | Pass |
| AP-11 | app | quantity 0 | Rejected: "whole number of at least 1" | As expected | Pass |
| AP-12 | app | quantity 2.5 | Rejected: "whole number of at least 1" | As expected | Pass |
| AP-13 | app | discount_rate -0.1 | Rejected: "between 0 and 1" | As expected | Pass |
| AP-14 | app | discount_rate 1.5 | Rejected: "between 0 and 1" | As expected | Pass |
| AP-15 | app | product_price "inf" | Rejected: "product_price: 1 missing or invalid values" | As expected (first run: accepted and scored; fixed, see KI-1) | Pass |
| AP-16 | app | Analyst (Central America) uploads 1 Western Europe row | Rejected: "1 rows are outside your region (Central America)" | As expected | Pass |
| AP-17 | app | Admin uploads rows from 3 regions | Accepted | Accepted | Pass |
| AP-18 | app | score on a valid upload with the saved model | Probabilities between 0 and 1 | As expected | Pass |
| AP-19 | app | score on 50 real rows | Level High exactly when model.predict is 1, i.e. probability >= 0.397; only High/Low | As expected | Pass |
| AP-20 | app | score with a model input column missing | KeyError | KeyError raised | Pass |
| AP-21 | app (AppTest) | Log in as analyst with a wrong password | Error "Wrong username or password."; not logged in | As expected | Pass |
| AP-22 | app (AppTest) | Log in as analyst; dashboard | "Region: Central America"; no region selector; top-risk table only Central America; order item count = Central America orders in the database | As expected | Pass |
| AP-23 | app (AppTest) | Analyst opens the order risk checker | Order region list offers only Central America | Only Central America | Pass |
| AP-24 | app (AppTest) | Log in as admin; dashboard | Region selector with "All regions" plus every region; sidebar "Regions: all" | As expected | Pass |

## Not covered by automated tests

These were checked by hand in the running app (`.venv/bin/streamlit run app.py`) on 2026-09-28:

- Batch scoring UI flow: the Streamlit file-upload widget, the success message and the results table
  (the checks behind them, `validate_upload` and `score`, are tested above).
- The "Download results (CSV)" button.
- Visual rendering of the dashboard charts (line charts per month, bar chart by shipping mode).
- The single-order risk checker end to end: pressing "Check risk" and the SHAP explanation shown in the UI
  (`explain_order` itself is tested in test_explain.py).
- Log out button.
- Full model training (`python -m src.train`) and the saved figures in `reports/figures/`; too slow for
  automated tests, so the training functions are tested on small synthetic data.
- Building the real database (`python -m src.db`); tested on a temporary database instead.

## Known issues found

| ID | Where | Issue | Found by | Fix (applied 2026-09-30) | Status |
|---|---|---|---|---|---|
| KI-1 | app.py, `validate_upload` | An uploaded product_price of `inf` was accepted: `pd.to_numeric` turns "inf" into infinity, which is not missing and not negative, so the row was scored. | AP-15 | Infinite values in the numeric columns are turned into missing values, so they are reported as "missing or invalid" and the file is rejected. | Fixed, AP-15 passes |
| KI-2 | src/db.py, `save_predictions` | If one row in a batch failed (for example an unknown order_item_id), the rows inserted before it were not rolled back and could be committed by the next commit on the same connection. | DB-35 | The insert runs inside `with conn:`, which commits on success and rolls back on an exception. | Fixed, DB-35 passes |

Minor observations (not bugs, no test marked):

- A blank quantity in an upload gives two messages ("quantity: 1 missing or invalid values" and
  "quantity: must be a whole number of at least 1") because NaN also fails the whole-number check.
- An upload whose first order_date cannot be parsed makes pandas print a "Could not infer format" warning;
  the row is still rejected correctly.
- Test note: importing app.py in a test (Streamlit "bare mode") leaves Streamlit's shared page marked as
  inside the login form, which would break the later AppTest runs in the same process. The test fixture
  clears that mark (`clear_bare_mode_form` in tests/test_app_logic.py). This comes from Streamlit and is
  not an app bug.
