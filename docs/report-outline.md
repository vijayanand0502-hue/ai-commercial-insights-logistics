# Report Outline

This outline maps the university's required report format (docs/university-guidelines.md) to where each part is drafted and which repo files it is built from.

Rule for all report text (CLAUDE.md): draft from repo facts only. Never invent numbers, names, dates, costs or references. Mark anything unknown as [FILL: what is needed].

**Files:**

| Part | File | Status |
|---|---|---|
| Part 1 | `docs/report/01_front_and_intro.md` | Drafted |
| Part 2 | `docs/report/02_design_and_implementation.md` | **Not written** |
| Part 3 | `docs/report/03_results_and_annex.md` | Drafted |
| Separate synopsis | The Synopsis section of Part 1, exported on its own | Drafted |

## Front matter (Part 1)

| # | University item | Section in draft | Built from | Status |
|---|---|---|---|---|
| F1 | Cover page as per format | Part 1, Cover Page | CLAUDE.md (title, programme, university) | Drafted; name, roll no., guide, date [FILL] |
| F2 | Acknowledgement | Part 1, Acknowledgement | AI-assistance paragraph at the end of Part 3 | Drafted; names [FILL]; paste the AI paragraph in |
| F3 | Certificate of guide (Annexure A) | Part 1, Certificate from Guide | docs/university-guidelines.md | Drafted; needs signature |
| F4 | Synopsis (3-4 pages, all required headings) | Part 1, Synopsis sections 1-10 | All modules, reports/model_comparison.csv, docs/test-report.md, docs/hardware-software.md | Drafted (about 2,000 words) |

## Main report

| # | University item | Section in draft | Built from | Status |
|---|---|---|---|---|
| M1 | Objective & scope of the project | Part 1, section 1 | CLAUDE.md scope, app.py | Drafted |
| M2 | Theoretical background | Part 1, section 2 | src/train.py, src/explain.py, src/db.py | Drafted; citations [FILL] |
| M3 | Definition of problem | Part 1, section 3 | src/features.py, docs/data-dictionary.md | Drafted |
| M4 | System analysis & design vis-a-vis user requirements | Part 2, section A (planned) | reports/figures/diagrams/architecture.png, CLAUDE.md requirements, docs/user-manual.md section 6 (roles) | **Not written** |
| M5 | System planning (PERT chart) | Part 2, section B (planned) | reports/figures/diagrams/pert.png, docs/diagrams/pert.md table, docs/ai-use-log.md dates | **Not written**; the chart still ends at Oct 5 and its durations are estimates |
| M6 | Process logic of each module | Part 2, section C (planned) | reports/figures/diagrams/ml_pipeline.png, src/data_prep.py, src/features.py, src/train.py, src/explain.py, src/db.py, app.py | **Not written** |
| M7 | Methodology adopted, system implementation, hardware & software | Part 2, section D (planned) | docs/hardware-software.md, requirements.txt, docs/setup.md | **Not written**; CPU/RAM [FILL] |
| M8 | System maintenance & evaluation | Part 3, section 4 | reports/model_comparison.csv, confusion matrix, figure 10 | Drafted |
| M9 | Cost and benefit analysis | Part 3, section 5 | Qualitative | Drafted; money [FILL] |
| M10 | Detailed life cycle of the project | Part 3, section 6.1 | docs/ai-use-log.md | Drafted |
| M11 | ERD, DFD | Part 3, sections 6.2-6.3 | reports/figures/diagrams/erd.png, dfd_level0.png, dfd_level1.png | Drafted (diagrams done) |
| M12 | Input and output screen design | Part 3, section 6.4 | reports/figures/screenshots/*.png | Drafted (screenshots done) |
| M13 | Process involved | Part 2, section C (planned), or a short section before M8 | reports/figures/diagrams/ml_pipeline.png | **Not written** |
| M14 | Methodology used for testing | Part 3, section 6.5 | tests/, docs/test-report.md | Drafted |
| M15 | Test report | Part 3, section 6.6 (summary) + docs/test-report.md (full) | docs/test-report.md | Drafted |
| M16 | Printout of the reports | Figures placed in the relevant sections (M4-M8) | reports/figures/01-10, reports/model_comparison.csv | Partial: figures 08-10 referenced in Part 3; EDA figures 01-07 not yet placed (suggest Part 2, section C, data preparation) |
| M17 | Printout of the code sheet | Appendix or separate printout | src/, app.py, tests/ | Not started |
| M18 | User/operational manual (security, access rights, backup, controls) | Part 3, section 7 (summary) + docs/user-manual.md (full) | docs/user-manual.md | Drafted |
| M19 | Limitations, future scope, conclusion | Part 3, sections 8-9 | All of the above | Drafted |

## Annexures (Part 3)

| # | University item | Section in draft | Status |
|---|---|---|---|
| A1 | Brief background of the organization | Annexure 1 | [FILL] or "NA" |
| A2 | Data dictionary (name, aliases, length, type; NA where not applicable) | Annexure 2 (+ docs/data-dictionary.md) | Drafted |
| A3 | List of abbreviations, figures, tables | Annexure 3 | Drafted; numbers [FILL] until Part 2 exists |
| A4 | References: bibliography and websites | Annexure 4 | Drafted; every entry "verify" |
| A5 | Soft copy of the project | Annexure 5 | Drive link [FILL] |
| A6 | Guide details | Annexure 6 | [FILL] |
| A7 | Certificate from guide | Annexure 7 | Drafted; needs signature |

## Planned structure of Part 2 (not yet written)

Suggested file: `docs/report/02_design_and_implementation.md`. Section numbers are to be settled when the parts are assembled (Part 1 uses 1-3; Part 3 currently uses 4-9).

**A. System Analysis and Design vis-a-vis User Requirements**
- User requirements: the two roles, four screens, security needs and local operation (CLAUDE.md, docs/user-manual.md).
- Functional and non-functional requirements, each traced to the component that meets it.
- Architecture: the architecture diagram and its component table (docs/diagrams/architecture.md).
- Database design: reference the ERD (M11).

**B. System Planning (PERT Chart)**
- The PERT diagram and its activity table (docs/diagrams/pert.md): activities, predecessors, o/m/p estimates, expected times and the critical path.
- Planned versus actual dates, from docs/ai-use-log.md.

**C. Process Logic of Each Module** (also covers M13, Process involved)
1. `src/data_prep.py`: the row filter, the leakage and drop column lists, cleaning steps and validation. Place EDA figures 01-07 here.
2. `src/features.py`: date parts, the 20 features, both preprocessors, and grouping of rare categories below 500 occurrences.
3. `src/train.py`: grouped split, baselines, grid search, threshold rule, and the saved `FixedThresholdClassifier`.
4. `src/explain.py`: PermutationExplainer, the additivity check, how the reason text is built, and the flag for rare values.
5. `src/db.py`: schema, scrypt hashing, dummy-hash timing protection, region filter by role, and bulk save in a transaction.
6. `app.py`: startup file check, login flow, one-time scoring, dashboard, checker with linked lists, batch validation rules, and one database connection per request.

**D. Methodology Adopted, System Implementation, Hardware and Software**
- Development method: iterative, one module at a time, with code review and tests after each module; AI-assisted, with the log kept in docs/ai-use-log.md.
- Implementation environment and versions (docs/hardware-software.md, requirements.txt).
- Installation and run steps (docs/setup.md).
- The fresh clone test result (docs/requirements-checklist.md, item 5.18).

## Assembly steps

1. Write Part 2 (sections A-D above).
2. Complete every [FILL] marker and verify every reference.
3. Join Parts 1-3 in the university order: front matter, synopsis, main report, annexures.
4. Number the figures and tables and update Annexure 3.
5. Export the full report and the separate synopsis to PDF.
6. Add the code printout; upload the soft copy to the drive link.
