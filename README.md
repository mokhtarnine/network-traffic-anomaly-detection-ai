# Network Traffic Anomaly Detection

**Topic 15 - Network Traffic Anomaly Detection Using Clustering**

## Project Overview

This project detects unusual network traffic using unsupervised machine learning. It uses the NSL-KDD dataset and applies clustering algorithms to separate traffic records according to their behavior.

The project uses K-Means with `k=5` as its anomaly-detection model. A Streamlit application provides an interactive workflow for uploading data, exploring it, preprocessing it, running anomaly detection, evaluating the clusters, and exporting the results.

## Problem Statement

Computer networks generate large amounts of traffic, making manual monitoring difficult. Suspicious connections can be hidden among thousands of normal records.

The goal of this project is to:

- Group network connections with similar behavior.
- Identify clusters or points that may represent attacks.
- Evaluate cluster quality with clustering metrics.
- Compare detected anomalies with NSL-KDD labels after clustering.
- Provide an interactive application for testing and presenting the model.

This is a clustering project, not a supervised classification project. The `label` column is removed before model training and is used only afterward to evaluate and interpret the clusters.

## Dataset

The project uses the NSL-KDD dataset, an improved version of the KDD Cup 1999 intrusion-detection dataset.

| File | Rows | Purpose |
|---|---:|---|
| `KDDTrain+.txt` | 125,973 | Training and model development |
| `KDDTest+.txt` | 22,544 | Final evaluation and application demo |

Each row contains:

- 41 network traffic features.
- One attack label.
- One difficulty value.

Important categorical features include:

- `protocol_type`
- `service`
- `flag`

The dataset can be downloaded from [NSL-KDD on Kaggle](https://www.kaggle.com/datasets/hassan06/nslkdd).

Place the files in:

```text
data/raw/KDDTrain+.txt
data/raw/KDDTest+.txt
```

## Project Structure

```text
ntd-ai/
|-- data/
|   |-- raw/
|   |   |-- KDDTrain+.txt
|   |   `-- KDDTest+.txt
|   `-- processed/
|-- models/
|   |-- kmeans_model.pkl
|   `-- preprocessor.pkl
|-- notebooks/
|   |-- 01_eda.ipynb
|   `-- 02_modeling.ipynb
|-- src/
|   |-- app/
|   |   |-- app.py
|   |   `-- database.py
|   |-- data/
|   |   |-- loader.py
|   |   `-- preprocessor.py
|   |-- eda/
|   |   `-- eda_analysis.py
|   |-- evaluation/
|   |   `-- metrics.py
|   `-- models/
|       `-- kmeans_model.py
|-- tests/
|   |-- test_loader.py
|   |-- test_metrics.py
|   |-- test_models.py
|   `-- test_preprocessor.py
|-- requirements.txt
`-- README.md
```

## Project Workflow

### 1. Data Loading

The loader reads the NSL-KDD train and test files, assigns the correct column names, and validates uploaded datasets.

### 2. Exploratory Data Analysis

EDA is used to understand:

- Dataset dimensions and column types.
- Missing and duplicated values.
- Normal and attack record distributions.
- Individual attack types.
- Categorical feature distributions.
- Numerical feature distributions.
- Correlations between numerical features.

Observed dataset information:

- Training shape: `(125973, 43)`
- Test shape: `(22544, 43)`
- Training attack classes: 23
- No missing values were found in the original NSL-KDD files.

### 3. Preprocessing

The clustering input is prepared as follows:

1. Remove `label`, `binary_label`, and `difficulty` from the model features.
2. Keep the labels separately for evaluation.
3. Encode `protocol_type`, `service`, and `flag` using `OneHotEncoder`.
4. Scale numerical features using `StandardScaler`.
5. Fit the preprocessor on training data.
6. Transform both training and test data with the same fitted preprocessor.

After preprocessing:

```text
X_train_processed: (125973, 122)
X_test_processed:  (22544, 122)
```

### 4. K-Means Clustering

K-Means groups records into a selected number of clusters. Several values of `k` were tested.

| Number of clusters | Silhouette Score | Davies-Bouldin Index |
|---:|---:|---:|
| 3 | 0.4203 | 1.0628 |
| 4 | 0.4254 | 0.9609 |
| 5 | **0.4404** | **0.8884** |

`k=5` was selected because it produced:

- The highest Silhouette Score.
- The lowest Davies-Bouldin Index.
- More detailed separation of network behavior.

The cluster numbers themselves do not mean normal or attack. After training, the labels are compared with each cluster to determine which cluster contains the highest concentration of attacks.

### 5. Evaluation

The project uses internal clustering metrics and label-based evaluation.

| Metric | Meaning |
|---|---|
| Silhouette Score | Measures how well records fit their clusters. Higher is better. |
| Davies-Bouldin Index | Measures similarity between clusters. Lower is better. |
| Adjusted Rand Index | Measures agreement between clusters and known labels. |
| Precision | Percentage of detected anomalies that are attacks. |
| Recall | Percentage of attacks successfully detected. |
| F1 Score | Balance between precision and recall. |

True labels do not participate in model training. They are used only after clustering to understand cluster contents and evaluate anomaly detection.

## Streamlit Application

The application provides a six-step workflow:

1. Upload an NSL-KDD dataset.
2. Explore the data with interactive EDA charts.
3. Preprocess categorical and numerical features.
4. Run K-Means with a selected value of `k` or the pre-trained `k=5` model.
5. Review metrics, clusters, anomalies, PCA visualization, and error analysis.
6. Export results to CSV or PDF and save the analysis history.

K-Means settings allow the user to:

- Choose the number of clusters.
- Use the saved pre-trained model with `k=5`.

## Installation

### 1. Open the project folder

```powershell
cd C:\Users\mokht\OneDrive\Desktop\AI_Project\ntd-ai
```

### 2. Create a virtual environment

```powershell
python -m venv .venv
```

### 3. Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

## Run the Application

From the project root, run:

```powershell
python -m streamlit run src\app\app.py
```

Then open:

[http://localhost:8501](http://localhost:8501)

For a quick demonstration, upload:

```text
data/raw/KDDTest+.txt
```

## Run the Tests

```powershell
python -m pytest
```

The tests cover:

- Dataset loading and validation.
- Data preprocessing.
- K-Means model helpers.
- Clustering evaluation metrics.

## Saved Models

The `models/` directory contains:

- `preprocessor.pkl`: fitted preprocessing pipeline.
- `kmeans_model.pkl`: trained K-Means model using `k=5`.

The pre-trained model must receive data transformed by the matching pre-trained preprocessor because it expects the same feature layout used during training.

## Technologies

- Python
- pandas
- NumPy
- scikit-learn
- Streamlit
- Plotly
- joblib
- SQLite
- fpdf2
- pytest

## Main Results

The experiments showed that `k=5` gave the best internal clustering quality among the tested K-Means configurations:

```text
Silhouette Score:     0.4404
Davies-Bouldin Index: 0.8884
```

These results indicate that five clusters provide better separation and lower similarity between clusters than the tested `k=3` and `k=4` configurations.

The model does not classify an individual connection using a fixed packet-number rule. It groups records based on all processed network features. The labels are then used to interpret which clusters are mostly normal traffic and which contain more attacks.

## Limitations

- Clustering does not guarantee that each cluster represents exactly one attack category.
- K-Means requires the number of clusters to be chosen in advance.
- K-Means requires the number of clusters to be selected before training.
- NSL-KDD is useful for academic experiments but does not represent all modern network attacks.
- Results may change when different preprocessing steps or parameter values are used.

## Future Improvements

- Improve K-Means parameter selection and cluster interpretation.
- Add automated parameter tuning.
- Improve feature selection and dimensionality reduction.
- Evaluate the system with newer network-security datasets using a separate compatible preprocessing pipeline.
- Add real-time traffic input.
- Deploy the Streamlit application online.

## Conclusion

This project presents a complete unsupervised machine-learning pipeline for network traffic anomaly detection. It includes data loading, EDA, preprocessing, K-Means clustering, evaluation, visual analysis, result export, saved models, automated tests, and an interactive Streamlit application.

The selected K-Means model uses `k=5`, based on the best observed Silhouette Score and Davies-Bouldin Index. NSL-KDD labels remain separate from training and are used only to evaluate and explain the discovered clusters.

## Author

**Said Louham**
