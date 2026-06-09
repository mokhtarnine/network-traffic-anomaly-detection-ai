# Network Traffic Anomaly Detection

**SUPMTI — Rabat | AI Capstone Project | Academic Year 2025–2026**
**Topic 15 — Network-traffic anomaly detection (Clustering)**
**Instructor: Pr. Soufiane HAMIDA**

---

## Problem Statement

Modern networks generate massive volumes of traffic, making manual anomaly detection impractical. This project applies unsupervised clustering algorithms (K-Means and DBSCAN) to automatically identify unusual traffic patterns in the NSL-KDD dataset, and presents the results through a fully interactive Streamlit web application.

---

## Architecture Assessment

The project follows the exact structure recommended in the capstone guide:

```
network-traffic-anomaly-detection-ai/
├── data/
│   ├── raw/                        ✅ KDDTest+.txt (NSL-KDD dataset)
│   └── processed/                  ⚠️  empty — processed arrays kept in memory only
├── notebooks/                      ❌ MISSING — no EDA or experiment notebooks
├── src/
│   ├── data/
│   │   ├── loader.py               ✅ File upload, validation, dataset summary
│   │   └── preprocessor.py        ✅ Encoding + scaling pipeline
│   ├── models/
│   │   ├── kmeans_model.py         ✅ Train, predict, load pre-trained
│   │   └── dbscan_model.py         ✅ Train, noise mask, cluster summary
│   ├── evaluation/
│   │   └── metrics.py              ✅ Silhouette, Davies-Bouldin, ARI, cross-tables
│   └── app/
│       ├── app.py                  ✅ Full Streamlit UI (5-step workflow)
│       └── database.py             ✅ SQLite analysis history
├── models/
│   ├── kmeans_model.pkl            ✅ Pre-trained K-Means (k=5)
│   └── preprocessor.pkl            ✅ Fitted ColumnTransformer
├── requirements.txt                ✅ All dependencies pinned
└── README.md                       ✅ This file
```

**The separation of concerns is clean** — each layer (data, models, evaluation, app) is independent and importable. The Streamlit app contains no business logic; it only calls the modules and renders results.

---

## What Is Implemented

| Capstone Criterion | Status | Details |
|---|---|---|
| Problem & dataset | ✅ Done | NSL-KDD dataset, 41 features, binary + multi-class labels |
| Preprocessing | ✅ Done | OneHotEncoding on categoricals, StandardScaler on numerics |
| EDA (code) | ✅ Done | Lives on `eda` branch (`src/eda/eda_analysis.py`) |
| Baseline model | ✅ Done | K-Means (k=5), pre-trained and saved to `models/` |
| Improved model | ✅ Done | DBSCAN with tunable eps and min_samples |
| Evaluation metrics | ✅ Done | Silhouette Score, Davies-Bouldin Index, Adjusted Rand Index |
| Cluster cross-table | ✅ Done | Normal vs Attack breakdown per cluster |
| Working demo | ✅ Done | Streamlit app on `http://localhost:8501` |
| Export results | ✅ Done | CSV + PDF report download |
| Analysis history | ✅ Done | SQLite persistence, view and delete entries |
| requirements.txt | ✅ Done | All dependencies pinned |
| Git workflow | ✅ Done | `main → dev → feature/streamlit-app` |

---

## What Still Needs to Be Implemented

### 1. EDA Notebook ❌ (High Priority — graded criterion)
The `eda` branch has `src/eda/eda_analysis.py` but no Jupyter notebook.
Need to create `notebooks/01_eda.ipynb` covering:
- Missing values analysis and duplicate removal
- Feature distribution plots (histograms, boxplots)
- Class balance visualization (normal vs attack ratio)
- Correlation heatmap + feature importance
- Protocol type, service, flag breakdowns

### 2. Modeling Notebook ❌ (High Priority — graded criterion)
Need `notebooks/02_modeling.ipynb` covering:
- K-Means elbow method (inertia vs k plot) to justify k=5
- Silhouette score vs k chart
- DBSCAN eps selection using k-distance graph
- Final model comparison table (K-Means vs DBSCAN)

### 3. Save Processed Data to Disk ⚠️ (Medium Priority)
`data/processed/` is empty. The pipeline preprocesses in memory only.
Need to save `X_train_processed.npy` and `X_test_processed.npy` for reproducibility.

### 4. Error Analysis ⚠️ (Medium Priority — explicitly in evaluation criteria)
No error analysis currently. Need:
- Misclassified record analysis (which attack types end up in "normal" clusters)
- Confusion-style analysis: attack types distribution per cluster
- DBSCAN false-negative analysis (attacks not flagged as noise)

### 5. PDF Report ❌ (Required for submission)
The exam requires a written PDF report containing:
- Problem definition and dataset description
- Methodology (pipeline explanation)
- Results with plots and screenshots
- Conclusion and future improvements

### 6. Integrate EDA into Main Branch ⚠️ (Medium Priority)
`src/eda/eda_analysis.py` from the `eda` branch is not merged into `feature/streamlit-app`.
Either merge it or port the key functions.

### 7. KDDTrain+.txt Excluded from Git ⚠️ (Low Priority)
The 18 MB training file is in `.gitignore`. Submission ZIP should include it,
or provide a Kaggle/Drive download link in this README.

---

## Quick Start

### Install dependencies
```bash
pip install -r requirements.txt
```

### Run the web app
```bash
python -m streamlit run src/app/app.py
```
Then open **http://localhost:8501** and upload `data/raw/KDDTest+.txt`.

### Run the full training pipeline (from `modeling` branch)
```bash
python src/models/kmeans_clustering.py
```

---

## Dataset

**NSL-KDD** — an improved version of the KDD Cup 1999 dataset.

| File | Rows | Purpose |
|---|---|---|
| `KDDTrain+.txt` | 125,973 | Model training |
| `KDDTest+.txt` | 22,544 | Evaluation / demo |

Features: 41 input features (duration, protocol_type, service, flag, src_bytes, …) + label + difficulty.

Download: [NSL-KDD on Kaggle](https://www.kaggle.com/datasets/hassan06/nslkdd)

---

## Technology Stack

| Layer | Library |
|---|---|
| UI | Streamlit |
| ML | scikit-learn (KMeans, DBSCAN) |
| Data | pandas, NumPy |
| Visualization | Plotly |
| PDF export | fpdf2 |
| History storage | SQLite (stdlib) |
| Model persistence | joblib |

---

## Evaluation Metrics

| Metric | What it measures |
|---|---|
| **Silhouette Score** | How well separated the clusters are (−1 to 1, higher is better) |
| **Davies-Bouldin Index** | Average cluster similarity (lower is better) |
| **Adjusted Rand Index** | Agreement between predicted clusters and true labels |

---

## Git Workflow

```
main
└── dev
    └── feature/streamlit-app   ← active development
```

Branches: `main`, `dev`, `eda`, `modeling`, `app`, `wiki`, `feature/streamlit-app`

---

## Team
- Said Louham
