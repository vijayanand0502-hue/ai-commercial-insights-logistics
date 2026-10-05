# Requirements Checklist: Late Delivery Risk Prediction

Source: university "Guidelines for Submission of Project" (Major Project-Assignment 1).
Final submission: Mon Oct 5, 2026.
Last updated: 2026-09-30.

Owner: **Student** = you write or do it. **Claude** = supporting artifact produced with Claude Code, reviewed and understood by you.

**Status values:**
- **Done:** complete; the evidence is in the listed file.
- **Drafted:** text exists but needs your review and has [FILL] markers.
- **Partial:** part is done; see the note.
- **Not started**
- **Student to confirm:** only you know the status.

Report drafts are in `docs/report/`: Part 1 is `01_front_and_intro.md` and Part 3 is `03_results_and_annex.md`. Part 2 does not exist yet. See `docs/report-outline.md` for the full map.

## 1. Submission and general rules

| # | Requirement | How it is met | Owner | Status |
|---|---|---|---|---|
| 1.1 | Project report based on your own work | Parts 1 and 3 drafted from repo facts; Part 2 missing | Student | Partial |
| 1.2 | Report includes the software development | src/, app.py, tests/; described in the Part 1 synopsis and Part 3 sections 4 and 6; implementation chapter (Part 2) missing | Student + Claude | Partial |
| 1.3 | Soft copy on the university drive link | Upload repo zip + report PDF | Student | Not started |
| 1.4 | Summary/abstract submitted separately (3-4 pages) | Synopsis in Part 1 (about 2,000 words); export as a separate document | Student | Drafted |
| 1.5 | Guide with 3+ years IT experience | Guide details are [FILL] in Part 3, Annexure 6 | Student | Student to confirm |
| 1.6 | About 600 man-hours; topic in line with syllabus/industry | Hours not recorded in the repo | Student | Student to confirm |
| 1.7 | Individual work, no plagiarism | AI use recorded in docs/ai-use-log.md; AI-assistance disclosure drafted (end of Part 3) | Student | Drafted |

## 2. Summary/abstract contents (Part 1, Synopsis)

| # | Item | Where | Owner | Status |
|---|---|---|---|---|
| 2.1 | Name/title of the project | Synopsis section 1 | Student | Drafted |
| 2.2 | Statement of the problem | Synopsis section 2 | Student | Drafted |
| 2.3 | Why this topic was chosen | Synopsis section 3; personal reason is [FILL] | Student | Partial |
| 2.4 | Objective and scope | Synopsis section 4 | Student | Drafted |
| 2.5 | Methodology, including a project summary | Synopsis section 5 | Student | Drafted |
| 2.6 | Process description, supported by DFD/flowchart | Synopsis section 5; reports/figures/diagrams/dfd_level0.png, dfd_level1.png, ml_pipeline.png | Student (diagrams: Claude) | Drafted |
| 2.7 | Hardware and software used | Synopsis section 6; CPU/RAM/disk and Jupyter version are [FILL] | Student | Partial |
| 2.8 | Testing technologies used (pytest) | Synopsis section 7 | Student | Drafted |
| 2.9 | Resources and limitations | Synopsis section 8 | Student | Drafted |
| 2.10 | Contribution of the project | Synopsis section 9 | Student | Drafted |
| 2.11 | Conclusion (innovation, achievements, standout features) | Synopsis section 10; personal remark is [FILL] | Student | Drafted |

## 3. Project report format (in this order)

| # | Section | Supporting file | Owner | Status |
|---|---|---|---|---|
| 3.1 | Cover page (as per format) | Part 1; name, roll number, guide, date are [FILL] | Student | Drafted |
| 3.2 | Acknowledgement | Part 1; names are [FILL]; add the AI-assistance paragraph from Part 3 | Student | Drafted |
| 3.3 | Certificate of guide (Annexure A format) | Part 1 and Part 3 Annexure 7; needs guide signature | Student + Guide | Drafted |
| 3.4 | Synopsis | Part 1 | Student | Drafted |
| 3.5 | Objective and scope | Part 1, section 1 | Student | Drafted |
| 3.6 | Theoretical background (LR, tree models, metrics, SHAP) | Part 1, section 2; 8 citations are [FILL] | Student | Drafted |
| 3.7 | Definition of problem | Part 1, section 3 | Student | Drafted |
| 3.8 | System analysis and design vs user requirements | Diagram done: reports/figures/diagrams/architecture.png. Text (Part 2) missing | Student (diagram: Claude) | Partial |
| 3.9 | System planning (PERT chart) | reports/figures/diagrams/pert.png. Durations are estimates. Text (Part 2) missing | Student (diagram: Claude) | Partial |
| 3.10 | Process logic of each module | Diagram done: reports/figures/diagrams/ml_pipeline.png. Text (Part 2) missing | Student (diagram: Claude) | Partial |
| 3.11 | Methodology, system implementation, hardware and software | docs/hardware-software.md (CPU/RAM are [FILL]). Text (Part 2) missing | Student (list: Claude) | Partial |
| 3.12 | System maintenance and evaluation (retraining, model metrics) | Part 3, section 4 | Student | Drafted |
| 3.13 | Cost and benefit analysis | Part 3, section 5 (qualitative; money figures are [FILL]) | Student | Drafted |
| 3.14 | Detailed life cycle of the project | Part 3, section 6.1 | Student | Drafted |
| 3.15 | ERD | docs/diagrams/erd.md, reports/figures/diagrams/erd.png | Claude | Done |
| 3.16 | DFD (Level 0 and 1) | docs/diagrams/dfd.md, reports/figures/diagrams/dfd_level0.png, dfd_level1.png | Claude | Done |
| 3.17 | Input and output screen design | reports/figures/screenshots/ (5 screenshots); Part 3, section 6.4 | Student | Done |
| 3.18 | Process involved | reports/figures/diagrams/ml_pipeline.png; no separate report section yet | Student (diagram: Claude) | Partial |
| 3.19 | Methodology used for testing | Part 3, section 6.5 | Student | Drafted |
| 3.20 | Test report | docs/test-report.md (107 passed); summary in Part 3, section 6.6 | Claude (test-writer) | Done |
| 3.21 | Printout of the reports (charts, metrics, SHAP) | reports/figures/ (10 figures), reports/model_comparison.csv; not yet placed in the report | Student + Claude | Partial |
| 3.22 | Printout of the code | src/, app.py, tests/ | Student + Claude | Not started |
| 3.23 | User/operational manual: security, access rights, backup, controls | docs/user-manual.md; summary in Part 3, section 7 | Claude (docs-writer) | Done |
| 3.24 | Soft copy submitted with the hard-bound report | Drive link (replaces CD/floppy) | Student | Not started |

## 4. Annexures

| # | Item | Supporting file | Owner | Status |
|---|---|---|---|---|
| 4.1 | Background of the organization (if applicable, else NA) | Part 3, Annexure 1: [FILL] | Student | Not started |
| 4.2 | Data dictionary: data name, aliases, length, type; NA where not applicable | docs/data-dictionary.md; university-format table in Part 3, Annexure 2 | Claude (docs-writer) | Done |
| 4.3 | List of abbreviations, figures, tables | Part 3, Annexure 3; figure and table numbers are [FILL] until Part 2 exists | Student | Drafted |
| 4.4 | References: bibliography and websites (in the example format) | Part 3, Annexure 4; every entry is marked "verify" | Student | Drafted |
| 4.5 | Soft copy of the project | Drive link: [FILL] | Student | Not started |
| 4.6 | Guide details: name, full address, qualification, mobile, email | Part 3, Annexure 6: [FILL] | Student | Not started |
| 4.7 | Certificate from guide (Annexure A, signed) | Text in Part 3, Annexure 7; needs signature | Student + Guide | Drafted |

## 5. Software deliverables (scope from CLAUDE.md)

| # | Requirement | File | Status |
|---|---|---|---|
| 5.1 | DataCo Smart Supply Chain dataset in data/raw/ | data/raw/DataCoSupplyChainDataset.csv (git-ignored) | Done |
| 5.2 | Dataset profile and column classification (order-time / leakage / drop) | docs/data-dictionary.md | Done |
| 5.3 | Data preparation | src/data_prep.py | Done |
| 5.4 | EDA notebook with 7 charts | notebooks/01_eda.ipynb, reports/figures/01-07. The ai-use-log says the interpretation cells were left empty | Partial |
| 5.5 | Feature engineering in a scikit-learn Pipeline (fitted on training data only) | src/features.py | Done |
| 5.6 | Final feature list confirmed leakage-free by the student | Reviewed by code-reviewer and checked by tests (FE-04, DP-19); your own confirmation is not recorded in docs/ai-use-log.md | Student to confirm |
| 5.7 | Logistic regression baseline + one tree-based model | src/train.py | Done |
| 5.8 | Metrics: precision, recall, F1, ROC-AUC, confusion matrix; business metric justified | reports/model_comparison.csv, reports/figures/08-09; recall justified in Part 3, section 4.2 | Done |
| 5.9 | Best model saved | models/model.joblib (git-ignored; threshold 0.397) | Done |
| 5.10 | SHAP global and local explanations | src/explain.py, reports/figures/10 | Done |
| 5.11 | SQLite: users (hashed passwords, role, region), orders, predictions; parameterized queries | src/db.py | Done |
| 5.12 | Streamlit: login (admin, analyst) | app.py | Done |
| 5.13 | Streamlit: risk dashboard filtered by region access | app.py | Done |
| 5.14 | Streamlit: single-order risk checker with SHAP explanation | app.py | Done |
| 5.15 | Streamlit: batch CSV scoring with column/type validation | app.py, docs/sample_batch.csv | Done |
| 5.16 | pytest tests for all modules | tests/ (107 passed) | Done |
| 5.17 | README: setup, training, running the app and tests | README.md | Done |
| 5.18 | Fresh clone test passes | See "Fresh clone test" below | Done |

### Fresh clone test

**Run on:** 2026-09-30.

**How:** I cloned the repository into a temporary folder, applied the working-tree changes that were not yet committed, and followed docs/setup.md step by step:
- a new `.venv` with Python 3.12
- `pip install -r requirements.txt`
- the dataset copied into `data/raw/`
- `src.data_prep`, `src.train`, `src.explain` and `src.db`
- `pytest`
- starting the app

**Results:**

- **`src.data_prep`:** 172,762 rows × 22 columns. The clean CSV is byte-identical to the original.
- **`src.train`:** took about 4 minutes. Threshold 0.397; `reports/model_comparison.csv` is identical to the original.
- **`src.explain` and `src.db`:** ran without errors. The database has 172,762 orders and 2 users. It warned that the demo password environment variables were not set, which is expected.
- **Tests, first run:** 3 of 107 failed. The login tests open the database read-only, but a freshly built database has no saved predictions yet. The app saves them at the first login, so that save was refused.
  - The fix: the login tests now run on a private copy of `data/app.db`.
  - After the fix: **107 passed**, both in the clone and in the project. The real `data/app.db` was unchanged in both.
- **App:** started (health check "ok"). The first admin login scored and saved all 172,762 orders, and the dashboard showed 172,762 items, a 57.3% actual late rate and 71.5% predicted high risk.

## 6. Evaluation weights (for planning)

| Component | Weight |
|---|---|
| Presentation | 25% |
| Viva | 20% |
| Thesis/project report | 30% |
| Software: documentation | 10% |
| Software: code | 15% |
| **Pass mark** | **50% overall** |

## 7. What's missing (in priority order for the Oct 5 submission)

**Blocking: needed to submit**

1. **Part 2 of the report is not written** (items 3.8 to 3.11 and 3.18). It needs:
   - system analysis and design against user requirements
   - system planning with the PERT chart
   - process logic of each module
   - methodology, implementation and hardware/software
   - process involved

   The diagrams for all of these already exist.
2. **Personal details:**
   - your name and roll number
   - guide name and details, plus the guide's signature on the certificate
   - acknowledgement names
   - submission date
   - organization background (or "NA")
3. **References (item 4.4):** verify every entry marked "verify", fill in the in-text citations marked [FILL] in Part 1, section 2, and format them in the university style.
4. **Soft copy (items 1.3, 3.24, 4.5):** zip the repository (without data/ and models/, which are git-ignored) and upload it with the report PDF to the drive link.
5. **Code printout (item 3.22):** src/, app.py and tests/.
6. **Assemble and number the report:** join Parts 1 to 3, set figure and table numbers (Annexure 3), and export to PDF. The synopsis also goes separately (item 1.4).

**Content you must supply or confirm**

7. The reason for keeping HistGradientBoosting over logistic regression (Part 3, section 4.1). This is likely to be asked in the viva.
8. Your personal reason for choosing the topic (2.3) and your closing remarks (2.11, Part 3, section 9).
9. Hardware details: CPU, RAM, disk, machine model, and the Jupyter version (docs/hardware-software.md, Part 1 synopsis section 6).
10. Cost figures and man-hours (Part 3, section 5; item 1.6), or state that they are not applicable.
11. Confirm the leakage-free feature list (5.6).
12. Adjust the AI-assistance disclosure so it matches your own use (end of Part 3).

**Consistency fixes**

13. **Deadline references:** all documents now give Mon Oct 5, 2026.
14. **EDA notebook interpretation cells** are empty (5.4).
15. **Screenshots show your browser's bookmarks bar.** Consider cropping it before the report is printed.
16. **The analyst dashboard screenshot is scrolled.** The page title and "Region: Central America" line are cut off at the top; the sidebar still shows "Regions: Central America".
