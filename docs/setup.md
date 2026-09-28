# Setup

## Build the database

Run from the project root after `src.data_prep` has created `data/processed/orders_clean.csv`:

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
