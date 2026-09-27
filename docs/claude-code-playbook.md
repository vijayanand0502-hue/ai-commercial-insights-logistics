# Claude Code Playbook: Late Delivery Risk Prediction (Sep 27 - Oct 5, 2026)

Main session builds. Subagents review, test, and document.
Before every prompt: read the plan Claude gives, reply "go" only if you understand it.
Write that day's report section yourself every evening (at least 1 hour).

---

## Day 1 - Sun Sep 27: Pivot, setup, data

Prompt 1.1 (pivot)
```
Change of topic: the project is now late delivery risk prediction with no LLM and no API. I have replaced CLAUDE.md and the files in .claude/agents/ and docs/claude-code-playbook.md. Read them. Then: remove any Anthropic, Ollama, or API-key references from requirements.txt, .env.example, and other files; add scikit-learn, xgboost or lightgbm (recommend one and explain why), shap, joblib; create the models/ folder with .gitkeep and add models/* to .gitignore. Show me the changes before saving.
```

Prompt 1.2
```
Update docs/requirements-checklist.md for the new topic. Keep every university deliverable.
```

Download the DataCo Smart Supply Chain dataset from Kaggle into data/raw/ before the next prompt.

Prompt 1.3
```
Profile the dataset in data/raw/: columns, types, missing values, row count, class balance of the late delivery label, and file encoding. Then classify every column into: (a) known at order time, (b) recorded after shipping or delivery (leakage), (c) identifiers or personal data to drop. Show me the table. Do not clean yet.
```

Prompt 1.4
```
Write src/data_prep.py with small functions: load (handle encoding), drop leakage and personal-data columns I approved, parse dates, handle missing values, save to data/processed/. Explain each decision in one line.
```

Prompt 1.5 (subagents, in parallel)
```
Use the code-reviewer subagent to review src/data_prep.py, and in parallel use the docs-writer subagent to create docs/data-dictionary.md, marking each column as feature, excluded (leakage), or dropped.
```

---

## Day 2 - Mon Sep 28: EDA and features

Prompt 2.1
```
Create notebooks/01_eda.ipynb with 7 charts: late delivery rate overall, by shipping mode, by market/region, by product category, by customer segment, by order month, and scheduled shipping days vs late rate. Save charts to reports/figures/. Leave markdown interpretation cells empty for me.
```

Prompt 2.2
```
Write src/features.py: date features (month, weekday, quarter), encoding of categorical features, and a function returning the final feature list. Use a scikit-learn Pipeline so encoding is fitted on training data only. Explain why that prevents leakage.
```

Prompt 2.3 (subagent)
```
Use the code-reviewer subagent to review src/features.py, focusing on leakage.
```

---

## Day 3 - Tue Sep 29: Model training

Prompt 3.1
```
Explain in simple terms: logistic regression, random forest, and gradient boosting (the library we chose). Explain precision, recall, F1, and ROC-AUC with a logistics example, and which metric matters most for late delivery risk. Do not code yet.
```

Prompt 3.2
```
Write src/train.py: train/test split (stratified; explain whether a time-based split is better here), logistic regression baseline, the tree model with light tuning (small grid, cross-validation on training data only), a comparison table of all metrics, confusion matrix and ROC curve saved to reports/figures/, and save the best model pipeline to models/model.joblib.
```

Prompt 3.3 (subagent)
```
Use the code-reviewer subagent to review src/train.py, focusing on leakage, evaluation, and class imbalance.
```

---

## Day 4 - Wed Sep 30: Explainability and database

Prompt 4.1
```
Explain SHAP values in 8 simple lines: what a SHAP value means, global vs local explanations. Then write src/explain.py: global SHAP summary plot saved to reports/figures/, and a function that returns the top 5 factors for one order in plain language (e.g., "Standard Class shipping increased risk").
```

Prompt 4.2
```
Write src/db.py: SQLite database with tables users (id, username, password_hash, role, region), orders (processed data), predictions (order_id, risk_probability, risk_level, created_at). Use parameterized queries. Add 2 demo users: admin (all regions) and analyst (one region). Explain the password hashing choice.
```

Prompt 4.3 (subagents, in parallel)
```
Use the code-reviewer subagent to review src/explain.py and src/db.py, and in parallel use the docs-writer subagent to create the ERD in docs/diagrams/erd.md.
```

---

## Day 5 - Thu Oct 1: Streamlit app

Prompt 5.1
```
Build app.py in Streamlit with 4 screens: login (checks users table), risk dashboard (late rate KPIs, high-risk orders table, charts, filtered by the user's region access), single-order risk checker (form input -> probability, risk level, top 5 SHAP factors), and batch scoring (CSV upload with column validation -> results table and download). Admin sees all regions; analyst sees only theirs.
```

Prompt 5.2
```
Walk me through app.py section by section. After each section, ask me one question to check my understanding.
```

Fallback if behind schedule: drop batch scoring; keep login, dashboard, and single-order checker.

---

## Day 6 - Fri Oct 2: Testing

Prompt 6.1 (subagent)
```
Use the test-writer subagent to write and run tests for src/data_prep.py, src/features.py, src/train.py, src/db.py, and the app's validation and access-control logic, and produce docs/test-report.md.
```

Prompt 6.2
```
Fix the bugs the test-writer reported, one at a time. Explain each fix. Rerun the tests.
```

---

## Day 7 - Sat Oct 3: Documentation artifacts

Prompt 7.1 (subagent)
```
Use the docs-writer subagent to create: DFD Level 0 and Level 1, system architecture diagram, ML pipeline flow, PERT chart for this plan, docs/user-manual.md, and docs/hardware-software.md.
```

Prompt 7.2
```
Update docs/requirements-checklist.md: mark what is done, list what is missing.
```

Prompt 7.3
```
Update README.md: project summary, setup steps, how to train the model, run the app and tests, screenshots.
```

---

## Day 8 - Sun Oct 4: Viva and final review

Prompt 8.1 (viva practice, run as main session)
Terminal: `claude --agent viva-examiner`
Or in a new session: `Use the instructions in .claude/agents/viva-examiner.md and act as the examiner in this conversation.`

Prompt 8.2
```
Use the code-reviewer subagent to do a final review of the whole repo: leftover debug code, broken imports, missing docstrings, files that should not be committed.
```

Prompt 8.3
```
Review my report draft for gaps against docs/requirements-checklist.md. Point out missing sections and technical inaccuracies. Do not rewrite my text.
```

---

## Day 9 - Mon Oct 5: Submit
- Fresh clone test: clone into a new folder, create venv, install, train, run app and tests.
- Upload the soft copy to the university drive link.

---

## End of every day
```
Summarize today's changes, update docs/ai-use-log.md, and suggest a commit message.
```
