# Project: AI-Driven Late Delivery Risk Prediction and Explainable Insights System for Logistics

MS Data Science & AI major project, Chandigarh University. Final submission: Mon Oct 5, 2026.
No external APIs and no LLMs in the product. Everything runs locally.

## Owner and working rules
- I (the student) own this project. Claude assists; I review and must be able to explain every line in the viva.
- Before each task: give a 3-line plan and wait for my "go".
- After each task: give a 5-line plain-language explanation of what the code does and why.
- Keep code simple and readable. Prefer clarity over cleverness. No unnecessary abstractions.
- Work on one module at a time. Do not modify files outside the current task.
- Never commit or push without asking me.
- Append every significant task to docs/ai-use-log.md (date, task, tool/subagent used, what I reviewed or changed).
- Draft the report from repo facts only. Never invent numbers, names, dates, costs or references. Mark anything unknown as [FILL: what is needed].

## Scope (minimum viable version, do not expand without asking)
- Dataset: DataCo Smart Supply Chain (Kaggle), in data/raw/
- Target: late delivery risk (binary: late vs on time)
- Models: logistic regression baseline + one tree-based model (scikit-learn HistGradientBoostingClassifier)
- Metrics: precision, recall, F1, ROC-AUC, confusion matrix. Explain which metric matters most for the business.
- Explainability: SHAP global (feature importance) and local (per-order explanation)
- SQLite database: users (hashed passwords, role, region), orders, predictions
- Streamlit app: login (admin, analyst roles), risk dashboard, single-order risk checker with SHAP explanation, batch CSV scoring
- pytest tests + test report

## Data leakage rule (critical)
Only use features known at the time the order is placed.
Exclude anything recorded after shipping or delivery, for example actual shipping days, delivery status, shipping date, and any column derived from them.
Before training, list every feature used and confirm with me that none leak the outcome.

## Stack
Python 3.11+, pandas, numpy, scikit-learn (HistGradientBoostingClassifier as the tree model), shap, matplotlib, joblib, SQLite (sqlite3), Streamlit, pytest.
Ask before adding any other library.

## Structure
- data/raw, data/processed (git-ignored except .gitkeep)
- models/ (git-ignored; trained model files)
- src/ (data_prep.py, features.py, train.py, explain.py, db.py)
- app.py
- notebooks/ (01_eda.ipynb)
- tests/
- docs/ (requirements-checklist.md, data-dictionary.md, test-report.md, user-manual.md, hardware-software.md, ai-use-log.md, setup.md, diagrams/)
- reports/figures/

## Security
- Passwords stored hashed, never in plain text.
- Role-based access: analyst sees only their assigned region.
- Validate uploaded CSV columns and types before scoring.
- Parameterized SQL queries only.

## Subagents
- code-reviewer: review after each module
- test-writer: tests and test report
- docs-writer: diagrams, data dictionary, user manual
- viva-examiner: viva practice
