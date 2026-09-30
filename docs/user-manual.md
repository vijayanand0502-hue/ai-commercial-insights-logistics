# User Manual: Late Delivery Risk App

For end users (admin and analyst) and for the person who installs the app.
Everything runs on your own computer. The app does not call any external API or online service.

## 1. Prerequisites

| Item | Needed |
|---|---|
| Computer | macOS (tested on Darwin 27.0.0); see `docs/hardware-software.md` for hardware |
| Python | 3.11 or newer (tested with 3.12.6) |
| Python packages | From `requirements.txt` (pandas, numpy, scikit-learn, shap, matplotlib, joblib, streamlit, pytest) |
| Dataset | DataCo Smart Supply Chain dataset from Kaggle, file `DataCoSupplyChainDataset.csv` |
| Browser | Any modern web browser, to open the Streamlit page |

## 2. Installation and first build

Run every command from the project root folder.

1. Create the virtual environment and install the packages (the project `.venv` was created with `python3.12 -m venv .venv`):

   ```bash
   python3.12 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```

2. Put the dataset at `data/raw/DataCoSupplyChainDataset.csv`.

3. Prepare the data (creates `data/processed/orders_clean.csv`):

   ```bash
   .venv/bin/python -m src.data_prep
   ```

4. Train the model (creates `models/model.joblib`, `reports/model_comparison.csv` and figures 08 and 09 in `reports/figures/`):

   ```bash
   .venv/bin/python -m src.train
   ```

5. Optional: create the global SHAP chart `reports/figures/10_shap_global_importance.png`:

   ```bash
   .venv/bin/python -m src.explain
   ```

6. Build the database (creates `data/app.db`, loads all orders, adds the two demo users):

   ```bash
   .venv/bin/python -m src.db
   ```

   To choose your own demo passwords, set them on the first build:

   ```bash
   DEMO_ADMIN_PASSWORD=... DEMO_ANALYST_PASSWORD=... .venv/bin/python -m src.db
   ```

   If the variables are not set, the script prints a warning and uses the local defaults below.

## 3. Starting the app

```bash
.venv/bin/streamlit run app.py
```

Open the local address Streamlit prints in the terminal. Stop the app with Ctrl+C in the terminal.

The app needs `data/app.db` and `models/model.joblib`. The "Order risk checker" also reads `data/processed/orders_clean.csv`, so keep that file in place.

## 4. Logging in

The first screen is titled **Late Delivery Risk** and has the fields **Username** and **Password** and the button **Log in**.

Demo accounts (from `docs/setup.md`):

| Username | Role | Region access | Local default password |
|---|---|---|---|
| admin | admin | All regions | `admin123` (or `DEMO_ADMIN_PASSWORD` if set at build time) |
| analyst | analyst | Central America | `analyst123` (or `DEMO_ANALYST_PASSWORD` if set at build time) |

The default passwords are for local demos only.

If the login is wrong, the app shows **"Wrong username or password."** The same message is shown for an unknown username and for a wrong password, so the message does not reveal which usernames exist.

After login the sidebar shows:

- **Logged in as _username_ (_role_)**
- **Regions:** "all" for admin, or the analyst's region
- **Page:** a choice of **Dashboard**, **Order risk checker** and **Batch scoring**
- **Log out** button, which ends the session and returns to the login screen

The first page load after the database is built can take longer: the app scores every stored order once and saves the results in the `predictions` table. Later logins reuse the saved results.

## 5. Screens

### 5.1 Dashboard (header "Risk dashboard")

**Region filter**

- Admin: a **Region** drop-down with **All regions** plus every region in the data.
- Analyst: no drop-down; the page shows **Region: _your region_**. The data is already limited to that region by the database query.

**KPI tiles**

| Tile | Meaning |
|---|---|
| Order items | Number of order items in view (one row per product line of an order) |
| Actual late rate | Share of those items that were actually delivered late (historical label) |
| Predicted high risk | Share the model labels **High** (probability of late at or above 0.397) |
| Average predicted risk | Mean predicted probability of late |

Under the tiles a caption reminds you that the predictions cover all stored orders, including those the model was trained on, so they look better here than they would on new orders.

**Charts**

| Chart | Shows |
|---|---|
| Order items per month | Number of order items per calendar month |
| Actual late rate per month (%) | Late rate per month, in percent |
| Actual late rate vs average predicted risk by shipping mode (%) | Two bars per shipping mode: `actual_late_rate` and `predicted_risk`, in percent |

Months with no orders in the selected region are shown as 0 order items and a gap in the late-rate line (see Troubleshooting).

**Top 20 highest-risk order items**

A table of the 20 items with the highest predicted probability, with columns `order_item_id`, `order_date`, `order_region`, `order_country`, `shipping_mode`, `product_name`, `risk (%)` and `actually late` (Yes/No).

### 5.2 Order risk checker (header "Order risk checker")

Use this page to check one new order before it ships. Each list only offers values that appear in the orders you are allowed to see, and lists lower down only offer values that fit the choices above them.

| Section | Field | Notes |
|---|---|---|
| Destination | Order region | Analysts only see their own region |
| Destination | Order country | Only countries in the chosen region |
| Destination | Order state | Only states in the chosen country |
| Destination | Order city | Only cities in the chosen state |
| Destination | Market | Shown automatically; each region belongs to one market |
| Customer and product | Customer segment | |
| Customer and product | Customer country | |
| Customer and product | Customer state | Only states in the chosen customer country |
| Customer and product | Customer city | Only cities in the chosen customer state |
| Customer and product | Department | |
| Customer and product | Category | Only categories in the chosen department |
| Customer and product | Product | Only products in the chosen category |
| Order details | Order date | Defaults to today |
| Order details | Payment type | |
| Order details | Shipping mode | |
| Order details | Product price | Defaults to the usual (median) price of the chosen product; minimum 0 |
| Order details | Quantity | Whole number from 1 to 100; default 1 |
| Order details | Discount rate (0 to 1) | For example 0.05 = 5%; default 0 |

Press **Check risk**. The page then shows:

- **Probability of late delivery**: the model's probability, in percent.
- **Risk level**: **High** if the probability is 0.397 (39.7%) or more, otherwise **Low**.
- A line "The average order in the SHAP background sample has _X_% risk." This is the starting point of the explanation.
- While the explanation is computed, a spinner shows "Explaining the prediction (a few seconds)...". One explanation takes about 3 seconds.
- **Top factors**: up to 5 plain-language reasons (see section 7).

Checks made on this page are not saved to the database.

### 5.3 Batch scoring (header "Batch scoring")

Use this page to score many orders at once from a CSV file.

1. Prepare a CSV file with a header row containing these 18 columns (exact names, any order):

   | # | Column | Type | Rule |
   |---|---|---|---|
   | 1 | payment_type | Text | Not blank |
   | 2 | shipping_mode | Text | Not blank |
   | 3 | customer_segment | Text | Not blank |
   | 4 | customer_country | Text | Not blank |
   | 5 | customer_state | Text | Not blank |
   | 6 | customer_city | Text | Not blank |
   | 7 | market | Text | Not blank |
   | 8 | order_region | Text | Not blank; analysts: must equal their own region |
   | 9 | order_country | Text | Not blank |
   | 10 | order_state | Text | Not blank |
   | 11 | order_city | Text | Not blank |
   | 12 | category_name | Text | Not blank |
   | 13 | department_name | Text | Not blank |
   | 14 | product_name | Text | Not blank |
   | 15 | product_price | Number | Not negative, not infinite |
   | 16 | quantity | Number | Whole number, at least 1 |
   | 17 | discount_rate | Number | Between 0 and 1 |
   | 18 | order_date | Date | Must be a readable date, for example `2018-01-31 22:56:00` (the format of `orders_clean.csv`) |

   Extra columns are allowed and kept in the output but not used. If the file has a `late_delivery_risk` column, it is removed before scoring so the actual outcome cannot influence the model. Leading and trailing spaces in text are removed.

2. Choose the file with the **Orders CSV** uploader (only `.csv` files).

3. If the file is accepted, the page shows "Scored _N_ rows: _H_ high risk, _L_ low risk.", a table of all rows sorted from highest to lowest risk with two new columns `risk_probability` (0 to 1) and `risk_level` (High/Low), and a **Download results (CSV)** button that saves `risk_scores.csv`.

4. If the file is rejected, nothing is scored and the page shows "The file was not scored:" followed by one or more of these messages:

   | Message | Cause |
   |---|---|
   | Missing columns: _names_ | One or more of the 18 columns is absent or misspelled (checked first; no other checks run) |
   | The file has no rows. | Header only |
   | _column_: _N_ missing or invalid values | Blank text, a number or date that cannot be read, or an infinite number |
   | quantity: must be a whole number of at least 1 | Quantity below 1 or with decimals (a blank quantity also triggers this) |
   | product_price: must not be negative | Negative price |
   | discount_rate: must be between 0 and 1 | Discount rate below 0 or above 1 |
   | order_region: _N_ rows are outside your region (_region_) | Analyst uploaded rows for another region |

   A file that cannot be parsed at all shows "Could not read the file: _details_".

Batch results are not saved to the database. Download them if you need to keep them.

Text values the model has never seen (for example a new city) are accepted; the model treats them as unknown.

## 6. Roles and access rights

| Capability | Admin | Analyst |
|---|---|---|
| Log in | Yes | Yes |
| Dashboard data | All regions | Own region only (filtered in the SQL query) |
| Region drop-down on dashboard | Yes | No |
| Order risk checker: lists offered | Values from all orders | Values from own-region orders only |
| Batch scoring | Any region | Only rows whose `order_region` is the own region; otherwise the file is rejected |
| Download batch results | Yes | Yes |
| Create users or change passwords in the app | No (no such screen) | No |

Access is decided by role: only the `admin` role sees all regions. A non-admin account whose region is set to "All" sees no rows.

User accounts are managed outside the app. The demo accounts are created by `python -m src.db`; other accounts can only be added from Python with `add_user(conn, username, password, role, region)` in `src/db.py` (role must be `admin` or `analyst`). A password is set when the account is created; to change a demo password, delete `data/app.db` and rebuild (see `docs/setup.md`).

## 7. How to read a SHAP explanation

Each reason in **Top factors** has the form:

> _Feature_ _value_ increased/decreased risk by _X_ percentage points

for example "Shipping mode 'Standard Class' decreased risk by 12.3 percentage points" (illustrative numbers).

- The starting point is the average risk of the 100 background orders, shown in the line above the factors.
- Each factor pushes the risk up (increased) or down (decreased) from that average. The value is in **percentage points** of probability, not percent of the average.
- All 20 model features together add up exactly to the order's probability (the code checks this). The page only shows the 5 largest pushes, so the 5 shown do not add up to the full difference.
- Features with no effect are not listed, so you may see fewer than 5 reasons.
- "(a rare value, grouped with other rare values)" means the value appeared fewer than 500 times in the training data; the model does not know this specific value, only that it is rare.
- Date factors are shown as month name (Order month), day name (Order weekday) or quarter (Order quarter). The full order date itself is not used.
- A SHAP factor describes how the model reached its number. It does not prove that the factor causes late delivery.

## 8. Backup procedure

The app has no built-in backup function. Back up by copying files while the app is stopped (Ctrl+C in the terminal), so the database is not copied in the middle of a write.

| File | Contains | Can be rebuilt? |
|---|---|---|
| `data/app.db` | Users (password hashes, roles, regions), orders, saved predictions | Yes, with `python -m src.db`, but only demo users are recreated; other users would be lost. Predictions are recomputed at the next login. |
| `models/model.joblib` | Trained model with threshold | Yes, with `python -m src.train` (slow) |
| `data/processed/orders_clean.csv` | Clean data | Yes, with `python -m src.data_prep` |
| `data/raw/DataCoSupplyChainDataset.csv` | Original dataset | Re-download from Kaggle |
| `reports/` | Figures and model comparison table | Yes, by re-running the scripts |

Example backup to a dated folder:

```bash
mkdir -p backup/2026-10-03
cp data/app.db models/model.joblib data/processed/orders_clean.csv backup/2026-10-03/
```

To restore, stop the app, copy the files back to their original folders and start the app again.

These files are git-ignored (`data/*`, `models/*`), so they are not saved by git and must be backed up separately.

Re-running `python -m src.db` reloads the orders and deletes all saved predictions; existing users are kept.

## 9. Security controls

| Control | How it works (in the code) |
|---|---|
| Password hashing | Passwords are stored only as salted scrypt hashes (`hashlib.scrypt`, random 16-byte salt per user). Plain passwords are never stored. |
| Safe password check | Constant-time comparison (`hmac.compare_digest`); unknown usernames are checked against a dummy hash so the response time does not reveal which usernames exist. |
| Same login error | "Wrong username or password." for both unknown user and wrong password. |
| Role-based access | Admin sees all regions; analyst rows are filtered by region in the SQL query itself. |
| Parameterized SQL | Every query uses `?` placeholders, so user input cannot change the SQL. |
| Database constraints | Unique username; role must be `admin` or `analyst`; probability must be between 0 and 1; predictions must reference an existing order (foreign keys switched on). |
| Upload validation | Columns, types, ranges and region are checked before scoring; the outcome column is dropped. |
| Demo passwords from environment | `DEMO_ADMIN_PASSWORD` and `DEMO_ANALYST_PASSWORD` can replace the defaults at build time. |
| Local only | No external APIs; data stays on the machine. |
| Session | The logged-in user is kept in the Streamlit session; **Log out** removes it. |

Not included: account lockout after failed logins, password change screen, user management screen, audit log of logins.

## 10. Troubleshooting

| Problem | Cause and fix |
|---|---|
| "Missing: _file(s)_. From the project root run, in order: ..." | `data/processed/orders_clean.csv`, `models/model.joblib` or `data/app.db` does not exist; the app names which. Run the build steps in section 2 in the order shown (data_prep, train, db), using `.venv/bin/python`. |
| "Wrong username or password." | Check the spelling. If the database was built with `DEMO_ADMIN_PASSWORD` / `DEMO_ANALYST_PASSWORD`, the defaults do not work. To reset, delete `data/app.db` and rebuild. |
| Upload rejected | Read the list under "The file was not scored:" and fix each point (section 5.3). |
| "Could not read the file: ..." | The file is not a valid CSV (for example empty or wrong text encoding). Save it again as CSV (UTF-8). |
| Gaps or drops to zero in the monthly charts | Some regions have months with no orders at all. For example, Central America has no orders from June 2015 to December 2016. The charts show 0 order items and a blank late rate for those months rather than drawing a line across the gap. |
| First page after login is slow | The app is scoring all stored orders once (after each database build). |
| Dashboard shows old data after rebuilding the database | Orders are cached while the app runs. Stop the app and start it again. |
| The explanation takes a few seconds | Normal: each explanation takes about 3 seconds. |

## 11. Limitations

- Dashboard predictions include the orders the model was trained on (about 80% of stored orders), so the dashboard looks better than performance on new orders. Use the test-set figures in `reports/model_comparison.csv` for the real performance (tuned model: recall 0.795, precision 0.633, ROC-AUC 0.732).
- The model is driven mostly by shipping mode. In the global SHAP chart, shipping mode has a mean effect of more than 20 percentage points; every other feature is below 2. A baseline using shipping mode alone reaches a similar test ROC-AUC (0.739 vs 0.732).
- At the 0.397 threshold the model catches about 80% of late items, but about 37% of the items labelled High are actually on time (precision 0.633).
- All figures count order items, not whole orders.
- Single-order checks and batch results are not saved.
- Analysts are limited to one region; there is no screen to manage users or passwords.
- Values not seen in training (new cities, products, shipping modes) are treated as unknown, and values seen fewer than 500 times are grouped together.
