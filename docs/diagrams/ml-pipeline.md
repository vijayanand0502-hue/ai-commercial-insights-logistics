# ML Pipeline Flow

Source of truth: `src/data_prep.py`, `src/features.py`, `src/train.py`, `src/explain.py`, `app.py`; metrics from `reports/model_comparison.csv`.
Steps that exclude leakage are marked in red and labelled "LEAKAGE EXCLUSION".

```mermaid
flowchart TB
    RAW[("data/raw/DataCoSupplyChainDataset.csv")]

    subgraph PREP["1. Data preparation: python -m src.data_prep"]
        LOAD["Load CSV, encoding cp1252"]
        NS["LEAKAGE EXCLUSION: drop never-shipped orders (Order Status CANCELED, SUSPECTED_FRAUD)"]
        LEAK["LEAKAGE EXCLUSION: drop Days for shipping (real), Delivery Status, shipping date (DateOrders), Order Status"]
        PROFIT["LEAKAGE EXCLUSION: drop profit columns with uncertain timing (Benefit per order, Order Profit Per Order, Order Item Profit Ratio)"]
        OTHER["Drop personal data (8), ID codes (7), duplicates and formulas (5), empty or constant columns (4)"]
        STRIP["Strip spaces from text"]
        RENAME["Rename to snake_case; fail if any column is not on the approved list"]
        DATES["Parse order_date (format month/day/year hour:minute)"]
        BAD["Drop rows whose customer_state is a zip code"]
        MISS["Fail if any value is missing"]
        LOAD --> NS --> LEAK --> PROFIT --> OTHER --> STRIP --> RENAME --> DATES --> BAD --> MISS
    end

    CLEAN[("data/processed/orders_clean.csv: 172,762 rows x 22 columns")]

    subgraph FEAT["2. Features: src/features.py (inside the model Pipeline)"]
        DPARTS["Add order_month, order_weekday, order_quarter"]
        FLIST["20 model features: 14 categorical + 3 date parts + 3 numeric"]
        FEX["LEAKAGE EXCLUSION: ColumnTransformer drops everything else (order_id, order_item_id, order_date, target); scheduled_shipping_days left out (one-to-one with shipping_mode)"]
        ENC["Encoders fitted on training data only; categories under 500 rows grouped as infrequent"]
        DPARTS --> FLIST --> FEX --> ENC
    end

    subgraph SPLIT["3. Split: src/train.py"]
        SGK["StratifiedGroupKFold (5 folds, shuffle, seed 42): first fold = 20% test, rest = 80% train"]
        DISJ["LEAKAGE EXCLUSION: grouped by order_id; assert no order is in both train and test"]
        SGK --> DISJ
    end

    subgraph MODELS["4. Models on the training set (grouped 5-fold CV, ROC-AUC)"]
        MAJ["Baseline: always late (DummyClassifier most_frequent)"]
        SHIP["Baseline: shipping mode only (one-hot + LogisticRegression)"]
        LR["Logistic regression: one-hot + StandardScaler, max_iter 1000"]
        HGB["HistGradientBoosting: OrdinalEncoder + native categorical, early stopping off; GridSearchCV over 8 combinations (learning_rate, max_leaf_nodes, max_iter)"]
    end

    subgraph THR["5. Threshold tuning (training data only)"]
        OOF["cross_val_predict: out-of-fold probabilities of the best HGB pipeline"]
        PICK["Highest threshold with out-of-fold recall of at least 0.80: 0.397"]
        WRAP["FixedThresholdClassifier(FrozenEstimator(HGB pipeline), threshold 0.397)"]
        OOF --> PICK --> WRAP
    end

    subgraph EVAL["6. Evaluation on the 20% test set (per order item, positive class = late)"]
        MET["Tuned HGB: recall 0.795, precision 0.633, F1 0.705, accuracy 0.618, ROC-AUC 0.732"]
        OUT1[("reports/model_comparison.csv")]
        OUT2[("reports/figures/08_confusion_matrix.png, 09_roc_curves.png")]
        MET --> OUT1
        MET --> OUT2
    end

    MODELFILE[("models/model.joblib")]

    subgraph SHAPX["7. Explain: python -m src.explain"]
        BG["Background: 100 random training rows (seed 42)"]
        PE["shap PermutationExplainer on probability of late; additivity check"]
        GLOB["Global: mean absolute SHAP over 500 test rows"]
        LOC["Local: explain_order, top 5 reasons in percentage points"]
        BG --> PE
        PE --> GLOB
        PE --> LOC
    end

    OUT3[("reports/figures/10_shap_global_importance.png")]
    APP["8. Streamlit app.py: dashboard scores, order risk checker with SHAP, batch scoring"]

    RAW --> LOAD
    MISS --> CLEAN
    CLEAN --> SGK
    DISJ --> MAJ
    DISJ --> SHIP
    DISJ --> LR
    DISJ --> HGB
    FEAT -.->|"preprocessing step of"| LR
    FEAT -.->|"preprocessing step of"| HGB
    HGB --> OOF
    MAJ --> MET
    SHIP --> MET
    LR --> MET
    HGB --> MET
    WRAP --> MET
    WRAP --> MODELFILE
    MODELFILE --> PE
    GLOB --> OUT3
    MODELFILE --> APP
    LOC --> APP

    classDef leakage fill:#fde2e1,stroke:#c0392b,stroke-width:2px,color:#000
    class NS,LEAK,PROFIT,FEX,DISJ leakage
```

## Test-set results (from `reports/model_comparison.csv`)

Each row is one order item. Threshold 0.5 unless stated. The CSV labels the tuned row "threshold 0.40" because it rounds to 2 decimals; the saved threshold is 0.397 (test TR-13).

| Model | CV ROC-AUC (mean) | CV ROC-AUC (std) | Accuracy | Precision | Recall | F1 | Test ROC-AUC |
|---|---|---|---|---|---|---|---|
| Always late (baseline) | 0.500 | 0.000 | 0.573 | 0.573 | 1.000 | 0.728 | 0.500 |
| Shipping mode only (baseline) | 0.742 | 0.004 | 0.695 | 0.883 | 0.539 | 0.670 | 0.739 |
| Logistic regression | 0.742 | 0.005 | 0.694 | 0.859 | 0.557 | 0.676 | 0.731 |
| HistGradientBoosting | 0.740 | 0.005 | 0.690 | 0.833 | 0.574 | 0.679 | 0.732 |
| HistGradientBoosting (threshold 0.397), saved model | 0.740 | 0.005 | 0.618 | 0.633 | 0.795 | 0.705 | 0.732 |

## Step notes

| Step | What the code does | File |
|---|---|---|
| 1 | Removes never-shipped orders and every column recorded after shipping or delivery, plus profit columns whose timing is uncertain. `rename_columns` raises an error if any column outside the approved list survives, so a new column cannot reach the model without review. | `src/data_prep.py` |
| 2 | Date parts are made from `order_date`; `order_date` itself, the IDs and the target are dropped by `remainder="drop"`. The whole step is part of the Pipeline, so encoders are fitted on training folds only. | `src/features.py` |
| 3 | All items of one order stay on the same side of the split and in the same CV fold. | `src/train.py` |
| 4 | HistGradientBoosting is saved although its CV ROC-AUC ties with logistic regression, because it keeps one column per feature and SHAP maps directly to features. The best grid settings are printed at run time, not stored in a file. | `src/train.py` |
| 5 | The threshold is chosen from out-of-fold training predictions, never from the test set. | `src/train.py` |
| 7 | TreeExplainer is not used: it gave values that did not add up for HistGradientBoosting's native categorical splits. | `src/explain.py` |
| 8 | The app loads `models/model.joblib`, rebuilds the same 100-row background from `orders_clean.csv`, and creates a fresh explainer for every checked order. | `app.py` |
