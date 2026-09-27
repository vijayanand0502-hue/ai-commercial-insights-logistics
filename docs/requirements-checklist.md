# Requirements Checklist: Late Delivery Risk Prediction

Source: university "Guidelines for Submission of Project" (Major Project-Assignment 1).
Final submission: Mon Oct 5, 2026.

Owner: **Student** = you write or do it. **Claude** = supporting artifact produced with Claude Code, reviewed and understood by you.
Status: Not started / In progress / Done

## 1. Submission and general rules

| # | Requirement | How it is met | Owner | Day | Status |
|---|---|---|---|---|---|
| 1.1 | Project report based on your own work | Report written by the student | Student | Daily | Not started |
| 1.2 | Report includes the software development | src/, app.py, tests/ | Student + Claude | 1-6 | Not started |
| 1.3 | Soft copy on the university drive link | Upload repo zip + report PDF | Student | Oct 5 | Not started |
| 1.4 | Summary/abstract submitted separately (3-4 pages) | Separate document | Student | 8 | Not started |
| 1.5 | Guide with 3+ years IT experience | Guide confirmed | Student | - | Not started |
| 1.6 | About 600 man-hours; topic in line with syllabus/industry | Record hours in ai-use-log and your own log | Student | Daily | Not started |
| 1.7 | Individual work, no plagiarism | Own report text; AI use recorded in docs/ai-use-log.md | Student | Daily | Not started |

## 2. Summary/abstract contents

| # | Item | Owner | Status |
|---|---|---|---|
| 2.1 | Name/title of the project (stated at the start) | Student | Not started |
| 2.2 | Statement of the problem | Student | Not started |
| 2.3 | Why this topic was chosen | Student | Not started |
| 2.4 | Objective and scope (what the end user gains) | Student | Not started |
| 2.5 | Methodology, including a project summary | Student | Not started |
| 2.6 | Process description, supported by DFD/flowchart | Student (diagrams: Claude) | Not started |
| 2.7 | Hardware and software used | Student (list: docs/hardware-software.md) | Not started |
| 2.8 | Testing technologies used (pytest) | Student | Not started |
| 2.9 | Resources and limitations | Student | Not started |
| 2.10 | Contribution of the project | Student | Not started |
| 2.11 | Conclusion (innovation, achievements, standout features) | Student | Not started |

## 3. Project report format (in this order)

| # | Section | Supporting file | Owner | Day | Status |
|---|---|---|---|---|---|
| 3.1 | Cover page (as per format) | - | Student | 8 | Not started |
| 3.2 | Acknowledgement | - | Student | 8 | Not started |
| 3.3 | Certificate of guide (Annexure A format) | - | Student + Guide | 8 | Not started |
| 3.4 | Synopsis | - | Student | 8 | Not started |
| 3.5 | Objective and scope | - | Student | 1 | Not started |
| 3.6 | Theoretical background (LR, tree models, metrics, SHAP) | - | Student | 3-4 | Not started |
| 3.7 | Definition of problem | - | Student | 1 | Not started |
| 3.8 | System analysis and design vs user requirements | docs/diagrams/architecture.md | Student (diagram: Claude) | 7 | Not started |
| 3.9 | System planning (PERT chart) | docs/diagrams/pert.md | Student (diagram: Claude) | 7 | Not started |
| 3.10 | Process logic of each module | docs/diagrams/ml-pipeline.md, src/ | Student (diagram: Claude) | 7 | Not started |
| 3.11 | Methodology, system implementation, hardware and software | docs/hardware-software.md | Student (list: Claude) | 7 | Not started |
| 3.12 | System maintenance and evaluation (retraining, model metrics) | reports/figures/ | Student | 7 | Not started |
| 3.13 | Cost and benefit analysis | - | Student | 7 | Not started |
| 3.14 | Detailed life cycle of the project | - | Student | 7 | Not started |
| 3.15 | ERD | docs/diagrams/erd.md | Claude | 4 | Not started |
| 3.16 | DFD (Level 0 and 1) | docs/diagrams/dfd.md | Claude | 7 | Not started |
| 3.17 | Input and output screen design | Streamlit screenshots in reports/figures/ | Student | 5 | Not started |
| 3.18 | Process involved | docs/diagrams/ml-pipeline.md | Student (diagram: Claude) | 7 | Not started |
| 3.19 | Methodology used for testing | docs/test-report.md | Student | 6 | Not started |
| 3.20 | Test report | docs/test-report.md | Claude (test-writer) | 6 | Not started |
| 3.21 | Printout of the reports (charts, metrics, SHAP) | reports/figures/ | Student + Claude | 2-4 | Not started |
| 3.22 | Printout of the code | src/, app.py, tests/ | Student + Claude | 8 | Not started |
| 3.23 | User/operational manual: security, access rights, backup, controls | docs/user-manual.md | Claude (docs-writer) | 7 | Not started |
| 3.24 | Soft copy submitted with the hard-bound report | Drive link (replaces CD/floppy) | Student | Oct 5 | Not started |

## 4. Annexures

| # | Item | Supporting file | Owner | Status |
|---|---|---|---|---|
| 4.1 | Background of the organization (if applicable, else NA) | - | Student | Not started |
| 4.2 | Data dictionary: data name, aliases, length, type (Numeric/Alpha/Binary); NA where not applicable | docs/data-dictionary.md | Claude (docs-writer) | Not started |
| 4.3 | List of abbreviations, figures, tables | - | Student | Not started |
| 4.4 | References: bibliography and websites (in the example format) | - | Student | Not started |
| 4.5 | Soft copy of the project | Drive link | Student | Not started |
| 4.6 | Guide details: name, full address, qualification, mobile, email | - | Student | Not started |
| 4.7 | Certificate from guide (Annexure A, signed) | - | Student + Guide | Not started |

## 5. Software deliverables (scope from CLAUDE.md)

| # | Requirement | File | Day | Status |
|---|---|---|---|---|
| 5.1 | DataCo Smart Supply Chain dataset in data/raw/ | data/raw/ | 1 | Not started |
| 5.2 | Dataset profile and column classification (order-time / leakage / drop) | chat output, docs/data-dictionary.md | 1 | Not started |
| 5.3 | Data preparation | src/data_prep.py | 1 | Not started |
| 5.4 | EDA notebook with 7 charts | notebooks/01_eda.ipynb, reports/figures/ | 2 | Not started |
| 5.5 | Feature engineering in a scikit-learn Pipeline (fitted on training data only) | src/features.py | 2 | Not started |
| 5.6 | Final feature list confirmed leakage-free by the student | src/features.py | 2 | Not started |
| 5.7 | Logistic regression baseline + one tree-based model | src/train.py | 3 | Not started |
| 5.8 | Metrics: precision, recall, F1, ROC-AUC, confusion matrix; business metric justified | src/train.py, reports/figures/ | 3 | Not started |
| 5.9 | Best model saved | models/model.joblib | 3 | Not started |
| 5.10 | SHAP global and local explanations | src/explain.py, reports/figures/ | 4 | Not started |
| 5.11 | SQLite: users (hashed passwords, role, region), orders, predictions; parameterized queries | src/db.py | 4 | Not started |
| 5.12 | Streamlit: login (admin, analyst) | app.py | 5 | Not started |
| 5.13 | Streamlit: risk dashboard filtered by region access | app.py | 5 | Not started |
| 5.14 | Streamlit: single-order risk checker with SHAP explanation | app.py | 5 | Not started |
| 5.15 | Streamlit: batch CSV scoring with column/type validation (can be dropped if behind) | app.py | 5 | Not started |
| 5.16 | pytest tests for all modules | tests/ | 6 | Not started |
| 5.17 | README: setup, training, running the app and tests | README.md | 7 | Not started |
| 5.18 | Fresh clone test passes | - | Oct 5 | Not started |

## 6. Evaluation weights (for planning)

| Component | Weight |
|---|---|
| Presentation | 25% |
| Viva | 20% |
| Thesis/project report | 30% |
| Software: documentation | 10% |
| Software: code | 15% |
| **Pass mark** | **50% overall** |
