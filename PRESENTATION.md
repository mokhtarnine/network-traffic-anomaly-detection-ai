# Network Traffic Anomaly Detection
## AI Capstone Project — Topic 15
### SUPMTI Rabat · 2025–2026 · Pr. Soufiane HAMIDA

**Author:** Said Louham

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Problem Statement](#2-problem-statement)
3. [Dataset](#3-dataset)
4. [System Architecture](#4-system-architecture)
5. [Pipeline & Features](#5-pipeline--features)
   - [Step 1 — Data Loading & Validation](#step-1--data-loading--validation)
   - [Step 2 — Exploratory Data Analysis](#step-2--exploratory-data-analysis)
   - [Step 3 — Preprocessing](#step-3--preprocessing)
   - [Step 4 — K-Means Clustering](#step-4--k-means-clustering)
   - [Step 5 — Evaluation & Results](#step-5--evaluation--results)
   - [Step 6 — Export & History](#step-6--export--history)
6. [Streamlit Application](#6-streamlit-application)
7. [Model Selection & Results](#7-model-selection--results)
8. [Testing](#8-testing)
9. [Technology Stack](#9-technology-stack)
10. [Limitations & Future Work](#10-limitations--future-work)
11. [Conclusion](#11-conclusion)

---

## 1. Project Overview

> **Detect unusual network connections using unsupervised machine learning — no labels required at training time.**

This project builds a complete end-to-end pipeline for **network traffic anomaly detection** using the **NSL-KDD** benchmark dataset. It applies **K-Means clustering** (k = 5) to separate normal traffic from suspicious connections, then evaluates the results against the known attack labels.

An interactive **Streamlit web application** guides the user through every stage: upload → EDA → preprocess → detect → evaluate → export.

---

## 2. Problem Statement

| Challenge | Detail |
|-----------|--------|
| Scale | Networks generate thousands of records per second — manual inspection is impossible |
| Variety | Attacks differ widely in behavior (DoS, probes, R2L, U2R, …) |
| Unsupervised goal | No labels available at training time → clustering-based detection |

**Goals:**
- Group connections with similar behavior into clusters.
- Identify clusters with a high concentration of attacks.
- Measure cluster quality with internal metrics (Silhouette, Davies-Bouldin).
- Compare discovered clusters with known NSL-KDD labels for evaluation.
- Deliver an interactive demo application.

> Labels are **removed before training** and used **only after** to evaluate cluster quality.

---

## 3. Dataset

### NSL-KDD Dataset

An improved version of KDD Cup 1999 — the standard academic benchmark for intrusion-detection research.

| File | Rows | Use |
|------|-----:|-----|
| `KDDTrain+.txt` | 125,973 | Model training & development |
| `KDDTest+.txt` | 22,544 | Final evaluation & app demo |

### Features per record
- **41 network traffic features** (e.g., duration, src_bytes, dst_bytes, num_failed_logins, …)
- **3 categorical features:** `protocol_type`, `service`, `flag`
- 1 attack label + 1 difficulty score (excluded from training)

### Label statistics (training set)
- **23 distinct attack classes** (neptune, smurf, back, satan, ipsweep, …)
- No missing values in either file
- After preprocessing: **125,973 × 122 feature matrix**

---

## 4. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Streamlit Web Application                   │
│  Upload ──▶ EDA ──▶ Preprocess ──▶ Detect ──▶ Results ──▶ Export│
└────────────────────────────┬────────────────────────────────────┘
                             │
         ┌───────────────────┼────────────────────┐
         ▼                   ▼                    ▼
   src/data/           src/models/         src/evaluation/
   loader.py           kmeans_model.py     metrics.py
   preprocessor.py
         │                   │                    │
         ▼                   ▼                    ▼
   src/eda/            models/             src/app/
   eda_analysis.py     kmeans_model.pkl    database.py (SQLite)
                       preprocessor.pkl
```

### Project Layout

```
ntd-ai/
├── data/
│   ├── raw/          ← KDDTrain+.txt, KDDTest+.txt
│   └── processed/    ← X_train.npy, y_train.csv, preprocessor.pkl
├── models/           ← pre-trained kmeans_model.pkl + preprocessor.pkl
├── notebooks/
│   ├── 01_eda.ipynb
│   └── 02_modeling.ipynb
├── src/
│   ├── app/          ← app.py (Streamlit), database.py (SQLite)
│   ├── data/         ← loader.py, preprocessor.py
│   ├── eda/          ← eda_analysis.py
│   ├── evaluation/   ← metrics.py
│   └── models/       ← kmeans_model.py
└── tests/            ← 44 unit tests across 4 modules
```

---

## 5. Pipeline & Features

### Step 1 — Data Loading & Validation

**Module:** `src/data/loader.py`

- Accepts **CSV, Excel (.xlsx/.xls), and NSL-KDD .txt** files via drag-and-drop.
- Automatically assigns the 43 NSL-KDD column names.
- Validates schema, row count, and required columns.
- Computes a quick summary: row count, column count, null values, duplicates.
- Shows a preview of the first 5 rows.

**Validation feedback example:**
```
✓  125,973 rows · 43 columns · 0 nulls · 0 duplicates
```

---

### Step 2 — Exploratory Data Analysis

**Module:** `src/eda/eda_analysis.py`

Four interactive chart tabs, all rendered with **Plotly**:

| Tab | Charts |
|-----|--------|
| **Labels** | Traffic label bar chart (top 15) · Normal vs Attack donut · Top 15 attack types horizontal bar |
| **Categoricals** | Side-by-side bar charts for `protocol_type`, `service`, `flag` (top 10 each) |
| **Numerics** | Histogram grid for up to 20 numeric features (4 per row) |
| **Correlation** | Heatmap of the top 20 most-variable numeric features |

All charts use a consistent **Inter** font, white background, and hover tooltips — matching the Streamlit app's design system.

---

### Step 3 — Preprocessing

**Module:** `src/data/preprocessor.py`

| Stage | Transformer | Input | Output |
|-------|-------------|-------|--------|
| Encode categoricals | `OneHotEncoder(handle_unknown="ignore")` | `protocol_type`, `service`, `flag` | Sparse → dense columns |
| Scale numericals | `StandardScaler` | All remaining numeric columns | Mean 0, std 1 |
| Remove labels | Drop `label`, `binary_label`, `difficulty` | — | Clean feature matrix |

**Combined in a `ColumnTransformer` pipeline** (scikit-learn):

```
X_train: (125,973, 43) ──▶ fit_and_transform ──▶ (125,973, 122)
X_test:  (22,544,  43) ──▶ transform_only     ──▶ (22,544,  122)
```

Two modes in the app:
- **Fit new preprocessor** — fits on the uploaded data, saves `preprocessor.pkl`.
- **Use pre-trained preprocessor** — loads the saved pipeline for instant demo.

---

### Step 4 — K-Means Clustering

**Module:** `src/models/kmeans_model.py`

```python
KMeans(n_clusters=k, random_state=42, n_init=10)
```

**Key implementation details:**
- `n_init=10` — runs 10 random initialisations, picks the best.
- `random_state=42` — reproducible results.
- The slider in the app allows k from **2 to 20**.
- Pre-trained model uses **k = 5** (saved as `models/kmeans_model.pkl`).

**Anomaly cluster identification:**

After clustering, the cluster with the **highest attack ratio** is automatically flagged:

```
attack_ratio = attack_count / total_count   per cluster
anomaly_cluster = argmax(attack_ratio)
```

All records in that cluster are marked `is_anomaly = True`.

---

### Step 5 — Evaluation & Results

**Module:** `src/evaluation/metrics.py`

#### Internal Clustering Metrics (no labels needed)

| Metric | What it measures | Best value |
|--------|-----------------|------------|
| **Silhouette Score** | How well each record fits its own cluster vs neighbours | Higher → better (max 1.0) |
| **Davies-Bouldin Index** | Average similarity between each cluster and its most similar cluster | Lower → better (min 0.0) |

#### Label-Based Metrics (requires NSL-KDD labels)

| Metric | Formula | Meaning |
|--------|---------|---------|
| **Adjusted Rand Index** | Corrected-chance agreement between clusters and binary labels | Higher → better |
| **Precision** | TP / (TP + FP) | What fraction of flagged records are real attacks |
| **Recall** | TP / (TP + FN) | What fraction of all attacks were detected |
| **F1 Score** | 2 · P · R / (P + R) | Harmonic mean of precision and recall |

#### Visualisations in the Results Tab

- **Cluster bar chart** — records per cluster, anomaly cluster highlighted in red.
- **PCA 2D scatter plot** — up to 5,000 sampled points projected to 2 principal components, coloured by Normal / Anomaly.
- **Missed attack types (false negatives)** — horizontal bar chart showing which attack categories slipped through.
- **Attack types per cluster table** — how each attack type distributed across all clusters.
- **Cross-tables** — cluster × binary label and cluster × original label crosstabs with colour-gradient styling.

---

### Step 6 — Export & History

**Module:** `src/app/database.py` (SQLite) + `src/app/app.py` (FPDF2)

#### Export options

| Format | Content |
|--------|---------|
| **CSV download** | Original rows + `cluster` + `is_anomaly` columns |
| **PDF report** | Filename, algorithm, record count, anomaly count, anomaly rate, Silhouette, Davies-Bouldin, ARI, parameters |

#### Analysis History (SQLite)

- Every saved run is stored in `analysis_history.db`.
- Columns: timestamp, filename, algorithm, records, anomalies, ratio, Silhouette, DB-Index, ARI, params JSON.
- History table shows the last 20 runs, sortable.
- Individual rows can be deleted by ID.
- Auto-migration: the schema upgrades gracefully when new columns are added.

---

## 6. Streamlit Application

### Design System

| Element | Style |
|---------|-------|
| Metric cards | Rounded corners, subtle shadow, hover lift effect |
| Buttons | Rounded, 600-weight font, hover elevation |
| Download buttons | Blue tinted, border on hover |
| Tabs | Pill-style, active tab has white background |
| File uploader | Blue dashed border, hover highlight |
| Sidebar | Off-white background, right border |

### Step Progress Indicator

A live badge row shows the current position in the workflow:

```
▶ Upload   ✓ EDA   ● Preprocess   ● Detect   ● Results   ● Export
```

- **Grey ○** — not yet reached
- **Blue ▶** — currently active
- **Green ✓** — completed

### Sidebar Settings Panel

- K slider (2 – 20)
- "Use pre-trained model" checkbox
- Live summary after detection: anomaly count, rate, Silhouette Score

### Session State Management

Downstream state is automatically cleared when the dataset is re-uploaded, preventing stale results from a previous run being mixed with new data.

---

## 7. Model Selection & Results

### K-Means k Comparison

| k | Silhouette Score ↑ | Davies-Bouldin ↓ |
|---|------------------:|------------------:|
| 3 | 0.4203 | 1.0628 |
| 4 | 0.4254 | 0.9609 |
| **5** | **0.4404** | **0.8884** |

**k = 5 selected** — best on both internal metrics and provides finer-grained cluster separation.

### Why k = 5?

The NSL-KDD dataset contains traffic from roughly five behavioural groups:
- Normal traffic
- DoS attacks (e.g., neptune, smurf)
- Probe attacks (e.g., ipsweep, nmap)
- R2L attacks (e.g., warezclient)
- U2R attacks (e.g., buffer_overflow)

Five clusters align naturally with this structure without over-fragmenting the data.

### Saved Artefacts

| File | Description |
|------|-------------|
| `models/kmeans_model.pkl` | Trained K-Means (k = 5, n_init = 10) |
| `models/preprocessor.pkl` | Fitted ColumnTransformer (OHE + StandardScaler) |

> The pre-trained model and preprocessor **must be used together** — they share the same 122-feature layout.

---

## 8. Testing

**44 unit tests** across four modules, run with **pytest**.

| Test file | Module covered | What is tested |
|-----------|---------------|----------------|
| `tests/test_loader.py` | `src/data/loader.py` | File loading, column assignment, schema validation, error handling |
| `tests/test_preprocessor.py` | `src/data/preprocessor.py` | Fit-transform output shape, feature names, label separation, save/load round-trip |
| `tests/test_models.py` | `src/models/kmeans_model.py` | Training, prediction, anomaly mask, pre-trained model loading |
| `tests/test_metrics.py` | `src/evaluation/metrics.py` | Silhouette, Davies-Bouldin, ARI, precision, recall, F1, cluster tables |

Run all tests:

```powershell
python -m pytest
```

---

## 9. Technology Stack

| Library | Version | Role |
|---------|---------|------|
| **Python** | 3.10+ | Core language |
| **pandas** | — | DataFrame operations |
| **NumPy** | — | Array operations, PCA sampling |
| **scikit-learn** | — | KMeans, OneHotEncoder, StandardScaler, PCA, metrics |
| **Streamlit** | — | Interactive web application |
| **Plotly** | — | Interactive charts (bar, pie, scatter, heatmap, histogram) |
| **joblib** | — | Model serialisation (.pkl) |
| **SQLite** | built-in | Analysis history persistence |
| **fpdf2** | — | PDF report generation |
| **pytest** | — | Unit test framework |

---

## 10. Limitations & Future Work

### Current Limitations

| Area | Limitation |
|------|-----------|
| Algorithm | K-Means requires k to be chosen in advance |
| Clusters | One cluster ≠ one attack category — some attacks scatter across clusters |
| Dataset | NSL-KDD is academic; it does not represent all modern attack patterns |
| Sensitivity | Results vary with different preprocessing choices or random seeds |

### Planned Improvements

- **Automated k selection** — Elbow method, Gap statistic, or Silhouette scan integrated in the UI.
- **Additional algorithms** — DBSCAN (density-based, no k required), Isolation Forest.
- **Feature selection** — PCA or mutual information before clustering to reduce noise.
- **Real-time input** — Stream live PCAP traffic into the pipeline.
- **Online deployment** — Host the Streamlit app on Streamlit Cloud or a containerised server.
- **Modern datasets** — CICIDS 2017/2018 for broader attack coverage.

---

## 11. Conclusion

This project delivers a **complete, production-quality unsupervised ML pipeline** for network traffic anomaly detection:

| Component | Status |
|-----------|--------|
| Data loading & validation | ✓ |
| Interactive EDA (4 chart tabs) | ✓ |
| Preprocessing pipeline (OHE + Scaler) | ✓ |
| K-Means clustering (k selectable 2–20) | ✓ |
| Internal & label-based evaluation metrics | ✓ |
| PCA 2D visualisation | ✓ |
| Error analysis (FN breakdown by attack type) | ✓ |
| CSV & PDF export | ✓ |
| SQLite analysis history | ✓ |
| Pre-trained saved model | ✓ |
| 44 automated unit tests | ✓ |
| Streamlit interactive application | ✓ |

**Best model:** K-Means with **k = 5**
- Silhouette Score: **0.4404**
- Davies-Bouldin Index: **0.8884**

> The system demonstrates that unsupervised clustering can reliably separate normal and anomalous network traffic without requiring labelled training data — making it applicable to real-world scenarios where attack labels are unavailable.

---

*Network Traffic Anomaly Detection · Topic 15 · SUPMTI AI Capstone 2025-2026*
