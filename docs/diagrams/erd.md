# Entity-Relationship Diagram: SQLite database (data/app.db)

Source of truth: the `SCHEMA` string in `src/db.py`.

```mermaid
erDiagram
    users {
        INTEGER id PK "AUTOINCREMENT"
        TEXT username UK "NOT NULL"
        TEXT password_hash "NOT NULL, salt$hash (scrypt, hex)"
        TEXT role "NOT NULL, CHECK role IN ('admin','analyst')"
        TEXT region "NOT NULL, 'All' = every region"
    }

    orders {
        INTEGER order_item_id PK
        INTEGER order_id "NOT NULL"
        TEXT order_date "NOT NULL"
        TEXT order_region "NOT NULL, indexed (idx_orders_region)"
        TEXT order_country "NOT NULL"
        TEXT order_state "NOT NULL"
        TEXT order_city "NOT NULL"
        TEXT market "NOT NULL"
        TEXT customer_segment "NOT NULL"
        TEXT customer_country "NOT NULL"
        TEXT customer_state "NOT NULL"
        TEXT customer_city "NOT NULL"
        TEXT department_name "NOT NULL"
        TEXT category_name "NOT NULL"
        TEXT product_name "NOT NULL"
        REAL product_price "NOT NULL"
        INTEGER quantity "NOT NULL"
        REAL discount_rate "NOT NULL"
        TEXT payment_type "NOT NULL"
        TEXT shipping_mode "NOT NULL"
        INTEGER scheduled_shipping_days "NOT NULL"
        INTEGER late_delivery_risk "NOT NULL, historical label, not a model input"
    }

    predictions {
        INTEGER id PK "AUTOINCREMENT"
        INTEGER order_item_id FK "NOT NULL, REFERENCES orders(order_item_id)"
        REAL risk_probability "NOT NULL, CHECK BETWEEN 0 AND 1"
        TEXT risk_level "NOT NULL"
        TEXT created_at "NOT NULL, UTC ISO timestamp"
    }

    orders ||--o{ predictions : "scored as (order_item_id)"
    users }o..o{ orders : "logical only: region = order_region ('All' = every region)"
```

Note: the dotted `users`-`orders` link is not a foreign key. It is applied in the query code (`get_orders`, `get_predictions` in `src/db.py`), not by the database.

## Constraints and contents

| Table | Constraints | Holds |
|---|---|---|
| users | PK `id` (AUTOINCREMENT); UNIQUE `username`; CHECK `role IN ('admin','analyst')`; all columns NOT NULL | Login accounts: username, salted scrypt password hash, role and assigned region (`'All'` for admin). |
| orders | PK `order_item_id`; index `idx_orders_region` on `order_region`; all columns NOT NULL | Cleaned order items loaded from `data/processed/orders_clean.csv`. `late_delivery_risk` is the historical outcome label, used only for the dashboard late-rate KPIs and never as a model input. |
| predictions | PK `id` (AUTOINCREMENT); FK `order_item_id` -> `orders(order_item_id)`; CHECK `risk_probability BETWEEN 0 AND 1`; all columns NOT NULL | Model scores saved by the app: probability, risk level and UTC timestamp for one order item. |

SQLite enforces the foreign key only because `get_connection()` runs `PRAGMA foreign_keys = ON`.
