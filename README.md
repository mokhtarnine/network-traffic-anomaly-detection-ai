# Network Traffic Anomaly Detection

**SUPMTI — Rabat | AI Capstone Project | Academic Year 2025–2026**  
**Topic 15 — Network-traffic anomaly detection (Clustering)**  
**Instructor: Pr. Soufiane HAMIDA**

---

## Problem Statement

Modern networks generate massive volumes of traffic, making manual anomaly detection impractical. This project applies unsupervised clustering algorithms (K-Means and DBSCAN) to automatically identify unusual traffic patterns in the NSL-KDD dataset, and presents the results through a fully interactive Streamlit web application.

---

## Project Structure

```
network-traffic-anomaly-detection-ai/
├── data/
│   ├── raw/
│   │   └── KDDTest+.txt          NSL-KDD test dataset (22,544 rows)
│   └── processed/                Preprocessed arrays (generated at runtime)
├── notebooks/
│   ├── 01_eda.ipynb              Exploratory Data Analysis
│   └── 02_modeling.ipynb         K-Means elbow, DBSCAN k-distance, model comparison
├── src/
│   ├── data/
│   │   ├── loader.py             Upload handling, validation, dataset summary
│   │   └── preprocessor.py       Encoding + scaling pipeline, save/load processed
│   ├── eda/
│   │   └── eda_analysis.py       Plotly figures for EDA (labels, categoricals, heatmap)
│   ├── models/
│   │   ├── kmeans_model.py       Train, predict, load pre-trained K-Means
│   │   └── dbscan_model.py       Train, noise mask, cluster summary
│   ├── evaluation/
│   │   └── metrics.py            Silhouette, DB index, ARI, error analysis (P/R/F1)
│   └── app/
│       ├── app.py                Streamlit UI — 6-step workflow
│       └── database.py           SQLite analysis history
├── models/
│   ├── kmeans_model.pkl          Pre-trained K-Means (k=5, trained on KDDTrain+)
│   └── preprocessor.pkl          Fitted ColumnTransformer
├── requirements.txt
└── README.md
```

---

## Capstone Requirements — Completion Status

| Criterion | Requirement | Status |
|---|---|---|
| **Problem & Data** | Clear problem definition | ✅ |
| | Relevant public dataset (NSL-KDD) | ✅ |
| | EDA with visualizations | ✅ `notebooks/01_eda.ipynb` + in-app EDA tab |
| | Quality preprocessing | ✅ OneHotEncoding + StandardScaler |
| **Modeling** | Baseline algorithm | ✅ K-Means (k=5) — justified by elbow curve |
| | Improved algorithm | ✅ DBSCAN — eps chosen from k-distance graph |
| | Hyperparameter tuning | ✅ `notebooks/02_modeling.ipynb` |
| **Evaluation** | Task-correct metrics | ✅ Silhouette, Davies-Bouldin, Adj. Rand Index |
| | Error analysis | ✅ Precision, Recall, F1, missed attack types |
| | Model comparison table | ✅ K-Means vs DBSCAN in notebook |
| **Code & Reproducibility** | Clean, modular code | ✅ Separate data/models/evaluation/app layers |
| | README | ✅ This file |
| | Reproducible pipeline | ✅ Processed data saved to `data/processed/` |
| | Git history | ✅ Branched workflow |
| **Demo** | Working web app | ✅ Streamlit on `http://localhost:8501` |
| | Export results | ✅ CSV + PDF download |

### Still Needed Before Submission

| Item | Priority |
|---|---|
| PDF report (problem, methodology, results, screenshots) | Required |
| KDDTrain+.txt — add Kaggle download link below | Required |
| Run `notebooks/02_modeling.ipynb` fully and save cell outputs | Recommended |

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
Open **[http://localhost:8501](http://localhost:8501)** and upload `data/raw/KDDTest+.txt`.

### Run the notebooks
```bash
# EDA
jupyter notebook notebooks/01_eda.ipynb

# Modeling (elbow, k-distance, model comparison)
jupyter notebook notebooks/02_modeling.ipynb
```

---

## Dataset

**NSL-KDD** — improved KDD Cup 1999 dataset.

| File | Rows | Use |
|---|---|---|
| `KDDTrain+.txt` | 125,973 | Model training (excluded from git — 18 MB) |
| `KDDTest+.txt` | 22,544 | Evaluation & demo |

**Download KDDTrain+.txt:** [NSL-KDD on Kaggle](https://www.kaggle.com/datasets/hassan06/nslkdd)  
Place it in `data/raw/KDDTrain+.txt` before running the modeling notebook.

**Features:** 41 input features (duration, protocol_type, service, flag, src_bytes, …) + label + difficulty.

---

## Architecture

The code is organized in clean, independent layers with no circular dependencies:

```
Streamlit UI (src/app/app.py)
       │
       ├── src/data/loader.py          File upload + validation
       ├── src/data/preprocessor.py    Encoding + scaling
       ├── src/eda/eda_analysis.py     Plotly EDA figures
       ├── src/models/kmeans_model.py  K-Means train/predict
       ├── src/models/dbscan_model.py  DBSCAN train/predict
       ├── src/evaluation/metrics.py   Clustering + error metrics
       └── src/app/database.py         SQLite history
```

Each module is independently importable and testable. The Streamlit app contains no business logic — it only calls the modules and renders results.

---

## Evaluation Metrics

| Metric | What it measures |
|---|---|
| **Silhouette Score** | Cluster separation quality (−1 to 1, higher = better) |
| **Davies-Bouldin Index** | Average cluster similarity (lower = better) |
| **Adjusted Rand Index** | Agreement with true labels |
| **Precision** | Of all flagged anomalies, how many are real attacks |
| **Recall** | Of all attacks, how many were flagged |
| **F1 Score** | Harmonic mean of precision and recall |

---

## Technology Stack

| Layer | Library |
|---|---|
| UI | Streamlit |
| ML | scikit-learn (KMeans, DBSCAN) |
| Data | pandas, NumPy |
| Visualization | Plotly |
| PDF export | fpdf2 |
| Storage | SQLite (stdlib) |
| Model persistence | joblib |

---

## Git Workflow

```
main
└── dev
    └── feature/streamlit-app   ← active branch
```

Branches: `main`, `dev`, `eda`, `modeling`, `app`, `wiki`, `feature/streamlit-app`

---

## Team
- Said Louham
