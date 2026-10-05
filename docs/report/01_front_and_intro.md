# AI-Driven Late Delivery Risk Prediction and Explainable Insights System for Logistics

<!--
Draft generated from repository facts (code, docs/, reports/) on 2026-09-30.
Every [FILL: ...] marker must be completed by the student before submission.
Numbers are taken from reports/model_comparison.csv, docs/test-report.md, docs/hardware-software.md
and direct runs of the project code in the project .venv.
-->

---

## Cover Page

**AI-Driven Late Delivery Risk Prediction and Explainable Insights System for Logistics**

A project report submitted in partial fulfilment of the requirements for the degree of

**M.Sc (Data Science)**

Chandigarh University

Submitted by: Vijay Anand E

Roll No.: O23MSD110005

Under the guidance of: [FILL: guide name, designation]

[FILL: month and year of submission]

---

## Acknowledgement

I would like to express my sincere gratitude to my project guide, [FILL: guide name], for the guidance, encouragement and constructive feedback provided throughout this project.

I am also thankful to [FILL: names and roles of faculty members, programme coordinator or others who helped] for their support during the course of this work.

Finally, I thank [FILL: family, friends or colleagues to be acknowledged, if any] for their encouragement.

Vijay Anand E

O23MSD110005

---

## Certificate from Guide (Annexure A)

This is to certify that this project entitled "AI-Driven Late Delivery Risk Prediction and Explainable Insights System for Logistics" submitted in partial fulfillment of the degree of M.Sc (Data Science) to Chandigarh University done by [FILL: Mr./Ms.] Vijay Anand E, Roll No. O23MSD110005 is an authentic work carried out by him/her under my guidance. The matter embodied in this project work has not been submitted earlier for award of any degree or diploma to the best of my knowledge and belief.

| Signature of the student | Signature of the Guide |
|---|---|
| | Date- [FILL: date] |

---

## Synopsis

### 1. Title of the Project

AI-Driven Late Delivery Risk Prediction and Explainable Insights System for Logistics

### 2. Statement of the Problem

In order fulfilment, a delivery that arrives after its scheduled date affects customer satisfaction and creates follow-up work for the logistics team. In the dataset used for this project, the DataCo Smart Supply Chain dataset, 57.3% of the 172,762 shipped order items were flagged as late (`late_delivery_risk = 1`). When the risk of a late delivery is known only after shipping, the business can do little except react.

The problem I address is to estimate, **at the moment an order is placed**, the probability that an order item will be delivered late. The estimate must use only information that is available at that moment. For each prediction, the system must also explain in plain language which order characteristics raised or lowered the risk, so that an operations user can understand and act on it.

### 3. Why this Topic was Chosen

[FILL: personal reason for choosing this topic, for example work experience or interest in logistics analytics]

From a technical point of view, the topic combines several parts of the Data Science and AI curriculum in one end-to-end system:

- data preparation on a real, large dataset: 180,519 raw rows and 53 columns
- supervised classification with a baseline and a tree-based model
- evaluation with business-oriented metrics
- model explainability with SHAP
- a secure, role-based web application backed by a relational database

The topic also raises a practical issue that is common in industry: **data leakage**. The raw dataset contains several columns recorded after shipping, such as the actual shipping days and the delivery status, which would make a model look far better than it could be in real use. Designing the system so that these columns are never used was a central part of the work.

### 4. Objective and Scope of the Project

**Objectives**

1. Prepare the DataCo dataset for modelling. This means removing orders that never shipped, excluding every column recorded after shipping or delivery, and producing a clean, documented table.
2. Train and compare a logistic regression baseline and a tree-based model (scikit-learn `HistGradientBoostingClassifier`) to predict late delivery risk. The comparison also includes two simple reference baselines.
3. Choose a decision threshold that matches the business priority of catching late deliveries. I use recall as the main metric and set a target of at least 80% recall.
4. Explain the model globally (which features matter overall) and locally (the top five reasons behind a single order's risk) using SHAP.
5. Deliver the model to end users through a Streamlit web application with the following parts:
   - a login screen
   - a risk dashboard
   - a single-order risk checker
   - batch CSV scoring

   The application enforces role-based access: an admin sees all regions and an analyst sees only an assigned region.
6. Store users, orders and predictions in a SQLite database. Passwords are stored as salted hashes, and every query is parameterized.
7. Verify the system with automated tests (pytest) and document the results.

**Scope.** The project is a minimum viable, locally running system. It covers one dataset, one binary target, two main models, SHAP explanations, a SQLite database and a Streamlit application with two roles. It does not include demand forecasting, real-time integration with a live order system, external APIs or large language models. Everything runs on a single machine.

**Benefit to the end user.** An operations analyst can enter a new order, or upload a file of orders, and immediately see three things: the probability of late delivery, a High or Low risk level, and the main factors behind the prediction. This supports early action, for example choosing a different shipping mode or informing the customer.

### 5. Methodology (including a summary of the project)

The project follows a standard supervised machine learning workflow, implemented as separate Python modules in `src/` and a Streamlit application in `app.py`.

1. **Data preparation (`src/data_prep.py`).**
   - I load the raw file `DataCoSupplyChainDataset.csv` (Windows-1252 encoding, 180,519 rows, 53 columns). Its orders date from 1 January 2015 to 31 January 2018.
   - I remove 7,754 rows whose order status is CANCELED or SUSPECTED_FRAUD: these orders never shipped, so their "not late" label is meaningless.
   - I drop the leakage columns (actual shipping days, delivery status, shipping date, order status), the profit columns (their timing is uncertain), personal data, identifier codes and redundant columns.
   - After tidying the text, renaming the columns and removing three rows with invalid state values, the clean table has **172,762 order items, 22 columns and 62,894 orders**, with no missing values.
2. **Feature engineering (`src/features.py`).**
   - The model uses **20 features**: 14 categorical order-time attributes, 3 date parts derived from the order date (month, weekday, quarter) and 3 numeric attributes (product price, quantity, discount rate).
   - I excluded the scheduled shipping days because they map one-to-one to the shipping mode.
   - Categories seen fewer than 500 times in training are grouped as "infrequent".
   - All preprocessing is inside a scikit-learn Pipeline, so it is fitted on training data only.
3. **Model training and selection (`src/train.py`).**
   - The data is split 80/20 with a stratified split grouped by order, so no order appears in both the training set and the test set. This gives 138,209 training items (50,315 orders) and 34,553 test items (12,579 orders).
   - I trained four candidates:
     - an "always late" baseline
     - a shipping-mode-only baseline
     - logistic regression
     - `HistGradientBoostingClassifier`
   - The gradient boosting model was tuned with a grid of 8 settings, evaluated by order-grouped 5-fold cross-validation on ROC-AUC.
4. **Threshold tuning.**
   - Missing a late delivery is more costly than a false alarm, so I chose the decision threshold on out-of-fold training predictions. It is the highest threshold that still gives at least 80% recall: **0.397**.
   - On the untouched test set, the tuned model reaches:
     - **recall 0.795**
     - **precision 0.633**
     - **F1 0.705**
     - **ROC-AUC 0.732**
5. **Explainability (`src/explain.py`).**
   - I use SHAP's PermutationExplainer on the predicted probability, with 100 training rows as background.
   - It produces a global importance chart and, for any single order, the top five factors in percentage points of risk.
6. **Database (`src/db.py`) and application (`app.py`).**
   - A SQLite database stores users, orders and predictions.
   - The Streamlit application provides the login, dashboard, single-order checker and batch scoring screens, with admin and analyst roles.
7. **Testing.** The modules and the application logic are tested with pytest.

**Process description.** Information flows from the raw CSV file through data preparation to the clean dataset. The clean dataset is used to train and save the model and to build the database. The application reads the database and the saved model to serve users, and each user sees only the data their role permits. This flow is shown in the Data Flow Diagrams (Level 0 and Level 1, `reports/figures/diagrams/dfd_level0.png` and `dfd_level1.png`) and in the ML pipeline flowchart (`reports/figures/diagrams/ml_pipeline.png`).

The software was developed with the assistance of an AI coding assistant (Claude Code). I reviewed all code, and every significant AI-assisted task is recorded in `docs/ai-use-log.md`.

### 6. Hardware and Software Used

**Hardware:** Apple Mac running macOS (kernel Darwin 27.0.0); [FILL: machine model, CPU, RAM, free disk space]. No GPU is required; all training and scoring run on the CPU.

**Software:**

| Software | Version | Purpose |
|---|---|---|
| Python | 3.12.6 | Programming language |
| pandas | 3.0.6 | Data loading and cleaning |
| numpy | 2.5.3 | Numerical arrays |
| scikit-learn | 1.9.1 | Pipelines, logistic regression, HistGradientBoostingClassifier, cross-validation, metrics, threshold |
| shap | 0.52.0 | Model explanations |
| matplotlib | 3.11.2 | Charts and figures |
| joblib | 1.6.0 | Saving and loading the model |
| SQLite (Python `sqlite3`) | standard library | Database |
| Streamlit | 1.64.0 | Web application |
| pytest | 9.1.1 | Automated testing |
| Jupyter | [FILL: version] | Exploratory data analysis notebook |

No external APIs or large language models are used by the system itself.

### 7. Testing Technologies Used

I used **pytest** for automated testing, together with Streamlit's built-in testing tool (`streamlit.testing.v1.AppTest`), which runs the real application and logs in through its login form.

The test suite contains **107 tests**, and all 107 pass. The tests cover:

- data preparation, including checks that no leakage column survives
- feature engineering, including handling of unseen categories
- training utilities, including that no order appears in both the training and test sets, and the threshold rule
- the SHAP explanation code
- the database layer, including password hashing, SQL-injection attempts and region filtering
- the application's upload validation and role-based access control

Tests use small hand-made data and temporary databases so that project data is never modified. During testing, two defects were found and fixed:

- the upload check accepted an infinite price
- a failed batch of predictions was not rolled back

The full list is in `docs/test-report.md`.

### 8. Resources and Limitations

**Resources.**
- The public DataCo Smart Supply Chain dataset from Kaggle.
- A single personal computer.
- Open-source Python libraries.

No proprietary data or paid services were required.

**Limitations.**
- **The model is dominated by shipping mode.** A baseline that uses only the shipping mode reaches a test ROC-AUC of 0.739, which is practically the same as the full model's 0.732. In the global SHAP analysis, shipping mode has a mean effect of about 22 percentage points, and every other feature has an effect below about 2 points. In this dataset every First Class item is labelled late (26,512 of 26,512), which suggests the label depends strongly on how the scheduled delivery time is set for each mode.
- **There are many false alarms.** At the chosen threshold, precision is 0.633, so about 37% of orders flagged as High risk are in fact delivered on time.
- **The data is historical and has gaps.** It covers January 2015 to January 2018, and some regions have months with no orders at all. For example, Central America has none from June 2015 to December 2016.
- **The system is local only.** It is not connected to a live order system; new orders are entered by hand or uploaded as CSV files.
- **The dashboard's predictions include training orders.** Its figures are therefore more favourable than they would be on new orders.
- **Explanations are slow.** One explanation takes about 3 seconds.

### 9. Contribution of the Project

The project contributes a complete, reproducible and leakage-aware pipeline for late delivery risk. It runs from the raw data to a working application in which every prediction comes with a plain-language explanation.

Its main contributions are:

- A documented separation between features known at order time and information recorded after shipping, enforced in code and checked by tests.
- A decision threshold chosen on training data only and justified by the business priority of catching late deliveries.
- A finding of practical value: in this dataset, the shipping mode alone carries almost all of the predictive signal. This tells a logistics team where process improvements would have the most effect.
- A secure, role-based application: hashed passwords, parameterized SQL, and region-level access for analysts.

### 10. Conclusion

In this project I built an end-to-end system that predicts, at order time, the risk that an order item will be delivered late. On the test set it catches about 80% of late items (recall 0.795) and explains each prediction with SHAP.

The main strengths of the approach are:

- careful exclusion of information that would not be available at order time
- a threshold chosen for the business goal rather than the default of 0.5
- an explanation method that I verified to be correct for this model; the tree-specific SHAP method gave values that did not add up for its categorical splits, so I used the model-agnostic permutation method with an additivity check
- a working, tested application with role-based access

[FILL: any personal concluding remark on innovation or achievements the student wishes to add]

---

## 1. Objective and Scope of the Project

### 1.1 Objective

The objective of this project is to build a system that predicts the risk of late delivery for an order item at the time the order is placed, and explains that prediction. The specific objectives are:

1. **Leakage-free data.** Prepare a clean dataset from the DataCo Smart Supply Chain data that contains only information known when the order is placed. In particular, it excludes the actual shipping days, the delivery status, the shipping date and the order status.
2. **Predictive model.** Train a logistic regression baseline and a `HistGradientBoostingClassifier` model, compare them with two reference baselines, and select a model using order-grouped cross-validation.
3. **Business-aligned decision rule.** Treat recall on late deliveries as the primary metric, and choose the decision threshold on training data so that at least 80% of late deliveries are flagged. The resulting threshold is 0.397.
4. **Explainability.** Provide global feature importance and a per-order explanation listing the top five factors in percentage points of risk.
5. **Secure application.** Provide a Streamlit application with login, a risk dashboard, a single-order risk checker and batch CSV scoring. It has two roles: an admin sees all regions and an analyst sees only an assigned region. It stores data in SQLite, keeps passwords as salted hashes and uses parameterized queries.
6. **Verification.** Test all modules and the application logic with pytest and report the results.

### 1.2 Scope

**In scope:**

- One dataset (DataCo Smart Supply Chain, Kaggle) and one binary target, `late_delivery_risk` (late = 1, on time = 0), predicted per order item.
- Two main models (logistic regression and HistGradientBoosting), plus the "always late" and shipping-mode-only baselines for reference.
- Metrics: precision, recall, F1, ROC-AUC and the confusion matrix.
- SHAP global and local explanations.
- A SQLite database with three tables (users, orders, predictions).
- A Streamlit application with two roles (admin, analyst) and four screens (login, dashboard, order risk checker, batch scoring).
- Automated tests with pytest, and project documentation (data dictionary, diagrams, test report, user manual).

**Out of scope:**

- Demand forecasting or time-series prediction.
- Integration with live order-management or carrier systems.
- External APIs, cloud deployment and large language models in the product.
- Automatic retraining or monitoring of the model in production.

### 1.3 How the System Helps the End User

The intended users are logistics operations staff:

- An **analyst** is responsible for one region; in the demo setup the analyst is assigned Central America.
- An **admin** oversees all regions.

With the system, a user can:

- **See the risk picture on the dashboard.** It shows the actual late rate, the share of orders predicted as High risk, monthly trends, the late rate by shipping mode, and the 20 highest-risk order items.
- **Check a new order before it ships.** The user enters its details and receives the probability of late delivery, a High or Low risk level, and the top five reasons.
- **Score many orders at once.** The user uploads a CSV file, which is validated before scoring, and downloads the results.

Because an analyst can only see and score orders for their own region, the system also supports data separation between teams.

---

## 2. Theoretical Background

### 2.1 Late Delivery Risk in Logistics

In order fulfilment, each order has a scheduled delivery time. The scheduled time usually depends on the shipping mode chosen by the customer: in this dataset, Same Day, First Class, Second Class or Standard Class. A delivery is late when the actual shipping time exceeds the scheduled time. Late deliveries reduce customer satisfaction and can lead to extra support contacts, refunds or lost repeat business [FILL: citation for the business impact of late deliveries, if one is used].

In the DataCo dataset, this outcome is recorded in the column `Late_delivery_risk`, which I renamed to `late_delivery_risk`. Its value is 1 if the item was delivered late and 0 otherwise. After cleaning, 57.3% of the 172,762 order items are labelled late. The late rate differs strongly by shipping mode:

| Shipping mode | Order items | Late rate |
|---|---|---|
| First Class | 26,512 | 100.0% |
| Second Class | 33,806 | 79.8% |
| Same Day | 9,293 | 47.9% |
| Standard Class | 103,151 | 39.8% |

**Data leakage** occurs when a model is trained with information that would not be available at prediction time. It makes the model appear more accurate than it can be in practice [FILL: citation on data leakage]. In this problem, the actual shipping days, the delivery status, the shipping date and the order status are all recorded after the order ships. They would reveal the outcome, so I excluded all of them.

### 2.2 Binary Classification

Predicting late delivery risk is a **binary classification** task. For each order item with features x, the model estimates the probability p = P(y = 1 | x) that the item will be late. A class label is then obtained by comparing p with a decision threshold t: predict "late" if p ≥ t, and "on time" otherwise. The model is learned from labelled historical examples (supervised learning).

To estimate how the model will behave on new orders, the data is split into a training set and a test set. In this dataset one order can contain several items that share the same customer, date and destination. If items of one order appeared in both sets, the test score would be optimistic. For this reason I used a **stratified, group-wise split**:

- It keeps every order entirely in one set.
- It keeps the late rate similar in both sets: 57.3% in each.

Hyperparameters were tuned with **k-fold cross-validation** (k = 5), using the same grouping by order.

### 2.3 Logistic Regression

Logistic regression is a linear model for binary classification [FILL: citation for logistic regression]. It computes a weighted sum of the input features and passes it through the logistic (sigmoid) function:

p = 1 / (1 + e^-(b0 + b1·x1 + ... + bk·xk))

The coefficients b are learned by maximising the likelihood of the training labels. Logistic regression is fast and interpretable, and it is a standard baseline. Because it is linear, the inputs need preparation:

- categorical features are **one-hot encoded**, one binary column per category
- numeric features are **standardised** to zero mean and unit variance

In this project, logistic regression reached a cross-validated ROC-AUC of 0.742 and a test ROC-AUC of 0.731.

### 2.4 Gradient Boosting and HistGradientBoostingClassifier

**Gradient boosting** builds an ensemble of decision trees one after another. Each new tree is fitted to correct the errors of the ensemble built so far, and the final prediction is the sum of all trees' outputs, converted to a probability [FILL: citation for gradient boosting].

scikit-learn's `HistGradientBoostingClassifier` is an efficient implementation. It first groups each numeric feature into at most 255 bins (histograms), which makes finding the best split much faster on large datasets [FILL: citation for scikit-learn / histogram-based gradient boosting]. It also supports **categorical features natively**: a split can send any subset of categories to the left or the right branch, so one-hot encoding is not needed.

In this project:

- Each categorical feature was converted to a single integer code (ordinal encoding) and marked as categorical.
- The model was tuned over learning rate (0.05, 0.1), maximum leaf nodes (15, 31) and number of iterations (200, 400). The selected setting was learning rate 0.1, 15 leaf nodes and 200 iterations.
- Its cross-validated ROC-AUC was 0.740 (standard deviation 0.005), within the cross-validation variation of logistic regression's 0.742. I kept the tree-based model as the final model.

### 2.5 Evaluation Metrics: Precision, Recall, F1 and ROC-AUC

With "late" as the positive class, each prediction on the test set falls into one of four groups:

- **true positives (TP):** late items predicted late
- **false positives (FP):** on-time items predicted late
- **true negatives (TN):** on-time items predicted on time
- **false negatives (FN):** late items predicted on time

These four counts form the **confusion matrix**. For the final model on the test set of 34,553 items, it is:

| | Predicted on time | Predicted late |
|---|---|---|
| **Actually on time** | 5,631 (TN) | 9,127 (FP) |
| **Actually late** | 4,062 (FN) | 15,733 (TP) |

From these counts:

- **Precision** = TP / (TP + FP) is the share of items flagged late that are actually late: 15,733 / 24,860 = 0.633.
- **Recall** = TP / (TP + FN) is the share of late items that the model catches: 15,733 / 19,795 = 0.795.
- **F1 score** = 2 · precision · recall / (precision + recall) balances the two: 0.705.
- **ROC-AUC** is the area under the Receiver Operating Characteristic curve, which plots the true positive rate against the false positive rate at every possible threshold. It equals the probability that a randomly chosen late item receives a higher predicted risk than a randomly chosen on-time item. A value of 0.5 means no ranking ability, and 1.0 means perfect ranking. It does not depend on the chosen threshold. The final model's test ROC-AUC is 0.732.

**Metric that matters most for the business.** Missing a late delivery (a false negative) means no early action is taken and the customer experiences the delay. A false alarm (a false positive) costs some extra attention from the operations team. I therefore treat **recall on late deliveries** as the primary metric, while reporting precision so that the cost of false alarms stays visible.

### 2.6 Choice of Decision Threshold

Most classifiers use a default threshold of 0.5. The default is not optimal when the costs of the two kinds of error differ. Lowering the threshold flags more items as late: recall rises and precision falls.

I chose the threshold on the training data only, so that the test set stays untouched:

1. I generated **out-of-fold predictions** using the order-grouped 5-fold cross-validation. Every training item then has a predicted probability from a model that did not see it.
2. I selected the **highest threshold at which out-of-fold recall is at least 80%**, which is **0.397**.

The model is saved with this threshold fixed (scikit-learn's `FixedThresholdClassifier`). On the test set it gives recall 0.795, just below the 0.80 target, which is expected when a threshold is transferred to new data. With the default threshold of 0.5, the same model reached recall 0.574 and precision 0.833 (`reports/model_comparison.csv`).

### 2.7 SHAP Explanations

SHAP (SHapley Additive exPlanations) explains an individual prediction by assigning each feature a contribution. The method is based on Shapley values from cooperative game theory [FILL: citation for SHAP and Shapley values]. The contributions are **additive**: the average prediction over a background sample (the baseline), plus the sum of all feature contributions, equals the model's prediction for that order.

- **Global explanation:** the mean absolute SHAP value of each feature over many orders shows which features matter most overall.
- **Local explanation:** the SHAP values of one order show which features raised or lowered that order's risk, and by how much.

In this project I explain the **predicted probability of late delivery**, so every contribution is expressed in percentage points of risk. I used SHAP's **PermutationExplainer**, with 100 training rows as background and a fixed random seed (42).

I did not use the faster TreeExplainer. In testing, it gave values that did not add up to the model's output for `HistGradientBoostingClassifier`'s native categorical splits, off by up to 3 log-odds. The PermutationExplainer only calls the model's prediction function, so it is correct for any model. The code checks the additivity property on every explanation.

Over 500 test order items, the global analysis shows:

- shipping mode has by far the largest effect, a mean of about 22 percentage points
- every other feature has a mean effect below about 2 points; the next largest are order state and order country

### 2.8 Role-Based Access Control and Password Security

**Role-based access control (RBAC)** grants permissions to roles instead of individual users; each user is assigned a role [FILL: citation for RBAC]. This system has two roles:

- **Admin:** can view and score orders from all regions.
- **Analyst:** is assigned one region and can view and score only orders from that region.

Access is decided by the user's role, not by the text of the region field. The region filter is applied inside the database query, so an analyst's screens never receive other regions' data. Batch files that contain rows from another region are rejected.

**Password storage.** Passwords are never stored in plain text. Each password is hashed with **scrypt**, a deliberately slow and memory-hard key-derivation function [FILL: citation for scrypt], using a random 16-byte salt per user. The stored value holds only the salt and the hash. At login, the entered password is hashed again with the stored salt, and the two hashes are compared in constant time. Two further measures protect the login:

- An unknown username triggers the same amount of hashing work as a wrong password, so response time does not reveal which usernames exist.
- All database queries use **parameterized statements**, so user input cannot change the SQL (protection against SQL injection).

---

## 3. Definition of Problem

### 3.1 Background

A logistics operation receives orders that differ in shipping mode, destination, product and customer. Some orders will be delivered later than scheduled. In the DataCo dataset this is the majority: 57.3% of the 172,762 shipped order items. Without a prediction, the operations team learns about a late delivery only after it has happened.

### 3.2 Problem Statement

Given the information available when an order is placed, the task is to estimate for each order item the probability that it will be delivered late. The system must:

- classify the item as High or Low risk
- explain which of the order's characteristics drove the estimate
- make this available securely to users according to their role and region

Formally, the task is supervised binary classification:

- **Unit of prediction:** one order item. The final dataset has 172,762 items belonging to 62,894 orders.
- **Target:** `late_delivery_risk`, 1 = late and 0 = on time.
- **Inputs:** 20 features known at order time:
  - 14 categorical: payment type, shipping mode, customer segment, customer country/state/city, market, order region/country/state/city, category, department and product
  - 3 date parts from the order date: month, weekday and quarter
  - 3 numeric: product price, quantity and discount rate
- **Excluded inputs:** everything recorded after shipping or delivery (actual shipping days, delivery status, shipping date, order status), profit columns whose timing is uncertain, identifiers and personal data.
- **Output:** a probability between 0 and 1, a risk level (High if the probability is at least 0.397, otherwise Low), and the top five contributing factors.

### 3.3 Requirements Derived from the Problem

1. **No leakage.** Only order-time features may be used, and no order may appear in both the training and the test data.
2. **Catch most late deliveries.** Recall on late items is the primary metric, with a target of at least 80%, chosen on training data only.
3. **Explainability.** Every single-order prediction must come with its main reasons, in terms a non-specialist can read.
4. **Security.** Users log in; passwords are stored as salted hashes; analysts see only their own region; SQL queries are parameterized; uploaded files are validated before scoring.
5. **Usability.** Users need a dashboard view, a way to check one new order, and a way to score a file of orders.
6. **Local operation.** The system runs on a single machine without external services.

### 3.4 Challenges Identified

- **Leakage-prone raw data.** Several attractive columns are recorded after shipping and had to be identified and removed.
- **Related rows.** Multiple items belong to the same order, which required grouped splitting and grouped cross-validation.
- **High-cardinality categories.** There are, for example, 3,585 order cities and 118 products; categories seen fewer than 500 times in training were grouped.
- **A dominant feature.** Shipping mode alone carries most of the signal, and the late label is 100% for First Class. This limits how much the other features can add.
- **Explanation correctness.** The fast tree-specific SHAP method was not correct for this model's categorical splits, so a slower model-agnostic method with an additivity check was required.
