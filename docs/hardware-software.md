# Hardware and Software

## Hardware used

| Item | Value |
|---|---|
| Machine | Apple Mac (model: to be filled in by the student) |
| Operating system | macOS, kernel Darwin 27.0.0 |
| CPU | To be filled in by the student (Apple menu > About This Mac) |
| RAM | To be filled in by the student |
| Free disk space | To be filled in by the student |
| GPU | Not used (all training and scoring run on the CPU) |

## Minimum and recommended requirements

**These are estimates, not measured values.** They are based on the dataset size (172,762 cleaned order items) and the workload in the code (grid search of 8 settings x 5 folds, SHAP PermutationExplainer, Streamlit); they have not been tested on smaller machines.

| Item | Minimum (estimate) | Recommended (estimate) |
|---|---|---|
| CPU | 64-bit dual-core | Quad-core or better (training is the slowest step) |
| RAM | 4 GB | 8 GB or more |
| Free disk space | 2 GB (virtual environment, dataset, processed CSV, database, model) | 5 GB |
| Operating system | macOS, Linux or Windows with Python 3.11+ (only macOS was tested; commands in the docs use macOS/Linux paths such as `.venv/bin/python`) | macOS (tested) |
| Display / browser | Any modern browser; wide screen helps (the app uses Streamlit's wide layout) | Same |
| Network | Not needed to run the app; needed once to download the dataset and install packages | Same |

## Software

Versions of the Python packages are pinned in `requirements.txt`; the Python and OS versions are from `docs/test-report.md` and `.venv/pyvenv.cfg`.

| Software | Version | Purpose in this project |
|---|---|---|
| macOS (Darwin) | 27.0.0 | Operating system |
| Python | 3.12.6 (project `.venv`) | Programming language; CLAUDE.md requires 3.11+ |
| pandas | 3.0.6 | Loading, cleaning and filtering tabular data |
| numpy | 2.5.3 | Numeric arrays; infinite-value check in upload validation |
| scikit-learn | 1.9.1 | Pipeline, encoders, LogisticRegression, HistGradientBoostingClassifier, StratifiedGroupKFold, GridSearchCV, FixedThresholdClassifier, metrics |
| shap | 0.52.0 | PermutationExplainer for global and per-order explanations |
| matplotlib | 3.11.2 | Confusion matrix, ROC curves and SHAP charts saved to `reports/figures/` |
| joblib | 1.6.0 | Saving and loading `models/model.joblib` |
| streamlit | 1.64.0 | Web app: login, dashboard, order risk checker, batch scoring |
| pytest | 9.1.1 | Automated tests (107 tests, see `docs/test-report.md`) |
| sqlite3 | Python standard library (no separate install) | Local database `data/app.db` |
| hashlib, hmac, os | Python standard library | scrypt password hashing, constant-time compare, random salts |
| Jupyter (for `notebooks/01_eda.ipynb`) | Not pinned in `requirements.txt`; version to be filled in by the student | Exploratory data analysis notebook |
| Web browser | Any modern browser | Displays the Streamlit app |

Dataset: DataCo Smart Supply Chain (Kaggle), file `DataCoSupplyChainDataset.csv`, encoding Windows-1252.

## External services

The product uses **no external APIs, no cloud services and no LLMs**. All data preparation, training, explanation, database access and the web app run locally on one machine. The only network traffic while the app runs is between the browser and the local Streamlit server.
