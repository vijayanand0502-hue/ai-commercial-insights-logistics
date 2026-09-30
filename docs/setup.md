# Setup

Run every command from the project root. Always use the project `.venv`, not conda.

## 1. Create the environment

```bash
python3.12 -m venv .venv
```

```bash
.venv/bin/pip install -r requirements.txt
```

## 2. Get the dataset

Download the DataCo Smart Supply Chain dataset from Kaggle and put `DataCoSupplyChainDataset.csv`
in `data/raw/` (git-ignored).

## 3. Prepare the data

```bash
.venv/bin/python -m src.data_prep
```

Creates `data/processed/orders_clean.csv`.

## 4. Train the model

```bash
.venv/bin/python -m src.train
```

Creates `models/model.joblib`, `reports/model_comparison.csv` and the model figures in `reports/figures/`.

## 5. SHAP figure (optional for the app)

```bash
.venv/bin/python -m src.explain
```

Creates `reports/figures/10_shap_global_importance.png`.

## 6. Build the database

```bash
.venv/bin/python -m src.db
```

This creates `data/app.db` (git-ignored), loads all orders and adds the two demo users.
Re-running it reloads the orders and clears saved predictions; existing users are kept.

## Demo accounts

| Username | Role | Region access | Password env var | Local default |
|---|---|---|---|---|
| admin | admin | All regions | `DEMO_ADMIN_PASSWORD` | `admin123` |
| analyst | analyst | Central America | `DEMO_ANALYST_PASSWORD` | `analyst123` |

The defaults are for local demos only. To use other passwords, set the variables before the first build:

```bash
DEMO_ADMIN_PASSWORD=... DEMO_ANALYST_PASSWORD=... .venv/bin/python -m src.db
```

Passwords are stored only as salted scrypt hashes. A user's password is set when the account is created, so to change a demo password, delete `data/app.db` and rebuild.

## 7. Start the app

```bash
.venv/bin/streamlit run app.py
```

Opens at http://localhost:8501. If `data/processed/orders_clean.csv`, `models/model.joblib` or `data/app.db`
is missing, the app says which one and stops. Restart the app after rebuilding the database.

## 8. Run the tests

```bash
.venv/bin/python -m pytest
```

See `docs/test-report.md`.
