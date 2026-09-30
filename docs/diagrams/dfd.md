# Data Flow Diagrams (DFD Level 0 and Level 1)

Source of truth: `src/data_prep.py`, `src/features.py`, `src/train.py`, `src/explain.py`, `src/db.py` and `app.py`.
Notation: rectangles = external entities, rounded boxes = processes, cylinders = data stores, labelled arrows = data flows.

## DFD Level 0 (context diagram)

```mermaid
flowchart LR
    SRC["DataCo CSV source (Kaggle)"]
    ADM["Admin"]
    ANA["Analyst"]
    SYS("0 Late Delivery Risk System")

    SRC -->|"raw order records (DataCoSupplyChainDataset.csv)"| SYS

    ADM -->|"username and password"| SYS
    ADM -->|"region choice"| SYS
    ADM -->|"new order details"| SYS
    ADM -->|"orders CSV (any region)"| SYS
    SYS -->|"login error or session"| ADM
    SYS -->|"dashboard: KPIs, charts, top 20 items (all regions)"| ADM
    SYS -->|"risk probability, risk level, top 5 SHAP factors"| ADM
    SYS -->|"scored table and risk_scores.csv, or validation errors"| ADM

    ANA -->|"username and password"| SYS
    ANA -->|"new order details"| SYS
    ANA -->|"orders CSV (own region only)"| SYS
    SYS -->|"login error or session"| ANA
    SYS -->|"dashboard: KPIs, charts, top 20 items (own region)"| ANA
    SYS -->|"risk probability, risk level, top 5 SHAP factors"| ANA
    SYS -->|"scored table and risk_scores.csv, or validation errors"| ANA
```

Note: the offline build scripts (`python -m src.data_prep`, `src.train`, `src.explain`, `src.db`) are run from the command line by whoever installs the system. The code has no role check on them, so no actor is attached to them in the diagrams.

| Element | Type | Description |
|---|---|---|
| Late Delivery Risk System | Process (0) | The whole system: data preparation, model training, SHAP explanations, SQLite database and the Streamlit app. Runs locally. |
| DataCo CSV source | External entity | The DataCo Smart Supply Chain dataset from Kaggle, saved as `data/raw/DataCoSupplyChainDataset.csv`. |
| Admin | External entity | User with role `admin`, region `All`. Sees every region and can narrow the dashboard to one region. |
| Analyst | External entity | User with role `analyst` and one assigned region (demo: Central America). Sees only that region; uploads with other regions are rejected. |
| Flows | Data flows | Login credentials, region choice (admin only), single-order inputs and CSV uploads go in; dashboard, risk results, SHAP factors, scored CSV and error messages come out. |

## DFD Level 1

```mermaid
flowchart TB
    SRC["DataCo CSV source (Kaggle)"]
    USR["Admin / Analyst"]

    D1[("D1 data/raw/DataCoSupplyChainDataset.csv")]
    D2[("D2 data/processed/orders_clean.csv")]
    D3[("D3 models/model.joblib")]
    D4[("D4 app.db users")]
    D5[("D5 app.db orders")]
    D6[("D6 app.db predictions")]
    D7[("D7 reports/figures")]
    D8[("D8 reports/model_comparison.csv")]

    P1("1.0 Prepare data")
    P2("2.0 Engineer features and train model")
    P3("3.0 Explain predictions")
    P8("8.0 Build database")
    P4("4.0 Authenticate user")
    P5("5.0 Show dashboard")
    P6("6.0 Check single order")
    P7("7.0 Score batch CSV")

    SRC -->|"downloaded CSV file"| D1
    D1 -->|"raw rows (cp1252)"| P1
    P1 -->|"clean order items, 22 columns"| D2

    D2 -->|"clean order items"| P2
    P2 -->|"HGB pipeline + threshold 0.397"| D3
    P2 -->|"confusion matrix, ROC curves"| D7
    P2 -->|"test metrics of 5 models"| D8

    D3 -->|"fitted pipeline"| P3
    D2 -->|"100 background rows, 500 test rows"| P3
    P3 -->|"global SHAP bar chart"| D7

    D2 -->|"clean order items"| P8
    P8 -->|"order rows"| D5
    P8 -->|"demo users with scrypt hashes"| D4
    P8 -->|"delete old predictions"| D6

    USR -->|"username and password"| P4
    D4 -->|"password_hash, role, region"| P4
    P4 -->|"login error message"| USR
    P4 -->|"session user: role, region"| P5
    P4 -->|"session user: role, region"| P6
    P4 -->|"session user: role, region"| P7

    D5 -->|"orders filtered by role and region"| P5
    D3 -->|"model for one-time scoring"| P5
    P5 -->|"probability and level for every stored order (only if table empty)"| D6
    D6 -->|"predictions joined to order_region, filtered"| P5
    USR -->|"region choice (admin only)"| P5
    P5 -->|"KPIs, monthly charts, shipping mode chart, top 20 table"| USR

    USR -->|"order details: 18 inputs"| P6
    D5 -->|"dropdown values from visible orders"| P6
    D3 -->|"model"| P6
    D2 -->|"100 background rows (training split)"| P6
    P6 -->|"one order row, pipeline, background"| P3
    P3 -->|"top 5 reasons in percentage points"| P6
    P6 -->|"probability, High/Low, average risk, top factors"| USR

    USR -->|"orders CSV upload"| P7
    D3 -->|"model"| P7
    P7 -->|"errors, or scored table and risk_scores.csv"| USR
```

Notes on the flows (from the code):

- Process 5.0: the one-time scoring (`ensure_predictions` in `app.py`) runs after login on whichever page is opened first, whenever the `predictions` table is empty. It is drawn under 5.0 because the dashboard is the only screen that reads `predictions`.
- Processes 6.0 and 7.0 do **not** write to D6. Single-order checks and batch results are shown and downloaded only, not saved.
- Process 7.0 drops a `late_delivery_risk` column if the upload contains one, so the actual outcome never reaches the model.
- Process 3.0 runs in two ways: offline (`python -m src.explain`, writes the global chart to D7) and online, called by 6.0 through `build_explainer` and `explain_order`.

| Element | Type | Description |
|---|---|---|
| DataCo CSV source | External entity | Kaggle dataset, downloaded by hand into `data/raw/`. |
| Admin / Analyst | External entity | App users. Admin: all regions plus region selector. Analyst: own region only. |
| 1.0 Prepare data | Process | `python -m src.data_prep`. Removes CANCELED and SUSPECTED_FRAUD orders, drops leakage, profit, personal, ID, duplicate and empty columns, strips text, renames to snake_case, parses `order_date`, drops zip-code `customer_state` rows, fails on missing values, saves D2. |
| 2.0 Engineer features and train model | Process | `python -m src.train` (uses `src/features.py`). Grouped stratified 80/20 split, two baselines, logistic regression, HistGradientBoosting with grid search, threshold tuning, test evaluation; saves D3, D7 figures 08 and 09, and D8. |
| 3.0 Explain predictions | Process | `src/explain.py`. shap PermutationExplainer on the probability of late, with an additivity check. Offline: global chart. Online: top 5 reasons for one order. |
| 8.0 Build database | Process | `python -m src.db`. Creates tables, clears predictions, reloads orders from D2, adds demo users if missing. |
| 4.0 Authenticate user | Process | Login form in `app.py`; `verify_user` checks the scrypt hash. Same error text for unknown user and wrong password. |
| 5.0 Show dashboard | Process | "Risk dashboard" page. Reads region-filtered orders and predictions; scores all stored orders once if D6 is empty. |
| 6.0 Check single order | Process | "Order risk checker" page. Scores one order and asks 3.0 for the top 5 SHAP factors. |
| 7.0 Score batch CSV | Process | "Batch scoring" page. Validates columns, types, ranges and region, then scores. Results are not saved. |
| D1 | Data store | Raw DataCo CSV (Windows-1252 encoding). |
| D2 | Data store | Clean order items, 22 columns. Also read at app run time for the SHAP background sample. |
| D3 | Data store | Saved model: `FixedThresholdClassifier(FrozenEstimator(pipeline))`, threshold 0.397. |
| D4 | Data store | `users` table: username, salted scrypt hash, role, region. |
| D5 | Data store | `orders` table: clean order items, indexed on `order_region`. |
| D6 | Data store | `predictions` table: order_item_id, risk_probability, risk_level, created_at (UTC). |
| D7 | Data store | Figures: `08_confusion_matrix.png`, `09_roc_curves.png`, `10_shap_global_importance.png` (figures 01 to 07 come from the EDA notebook, outside these processes). |
| D8 | Data store | Test-set comparison table of the five model rows. |
