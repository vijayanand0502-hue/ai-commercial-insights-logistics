# AI Use Log

| Date | Task | Tool / subagent | What I reviewed or changed |
|---|---|---|---|
| 2026-09-27 | Fresh start for new topic: git init, folder structure, .gitignore, venv; model library tested (XGBoost/LightGBM need libomp, chose scikit-learn option) | Claude Code (main session) | |
| 2026-09-27 | Created docs/requirements-checklist.md from the university guidelines | Claude Code (main session) | |
| 2026-09-27 | Switched tree model to scikit-learn HistGradientBoostingClassifier (CLAUDE.md lines 19 and 32), removed xgboost, pinned requirements.txt, restored docs/university-guidelines.md | Claude Code (main session) | |
| 2026-09-27 | Profiled DataCoSupplyChainDataset.csv (encoding, types, missing values, class balance) and classified all 53 columns into order-time / leakage / drop | Claude Code (main session) | |
| 2026-09-27 | Wrote src/data_prep.py (load cp1252, drop never-shipped rows and approved columns, strip text, rename, parse dates, missing check, save) and ran it: 172,765 rows x 24 columns | Claude Code (main session) | |
| 2026-09-27 | Prompt 1.5 (code-reviewer + docs-writer) not run here: project subagents were not loaded in this session because it started before .claude/agents/ was moved to the repo root. Moved to a new session. | Claude Code (main session) | |
| 2026-09-27 | Prompt 1.5: code review of src/data_prep.py (no critical issues, no leakage in 21 features; 6 suggested fixes pending my decision) and docs/data-dictionary.md (53 columns labelled Feature / Target / Key / Excluded - leakage / Dropped) | code-reviewer, docs-writer (parallel); main session computed raw column stats and cross-checked dictionary labels against data_prep.py | |
| 2026-09-27 | Applied review fixes to src/data_prep.py: missing-column guard, fail on missing values, drop 3 zip-code customer_state rows, load_processed() with parse_dates, dropped Order Item Total and Order Item Discount as formulas (option A). Re-ran: 172,762 x 22. Updated docs/data-dictionary.md to match | Claude Code (main session) | |
