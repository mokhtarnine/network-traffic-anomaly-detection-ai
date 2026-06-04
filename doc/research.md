# Network Traffic Anomaly Detection Web Application using Clustering

## AI Task Family
Clustering

---

# Problem Statement

Modern networks generate large amounts of traffic, making manual anomaly detection difficult.

This project detects unusual network traffic using clustering algorithms and presents the results through a simple web application.

---

# Objectives

- Detect abnormal traffic automatically
- Apply unsupervised learning
- Build a complete AI pipeline
- Visualize clusters and anomalies
- Provide a usable web application
- Produce reproducible results

---

# Dataset

Dataset source (choose one):

- CICIDS2017
- NSL-KDD
- UNSW-NB15
- Kaggle datasets

Dataset requirements:

- Public dataset
- Data preprocessing
- Exploratory Data Analysis (EDA)

---

# Complete AI Pipeline

Data

↓

Preprocessing

↓

Feature Engineering

↓

Model Training

↓

Evaluation

↓

Web Application

---

# Exploratory Data Analysis (EDA)

Perform:

- Missing values analysis
- Duplicate removal
- Distribution analysis
- Correlation analysis
- Feature selection
- Data visualization

---

# Data Preprocessing

Steps:

- Clean dataset
- Encode categorical values
- Normalize features
- Split datasets if necessary

---

# Modeling

Algorithms:

## Baseline
K-Means

## Improved Model
DBSCAN

Optional:

- Isolation Forest
- Gaussian Mixture

---

# Evaluation Metrics

Because this is clustering:

Primary metrics:

- Silhouette Score
- Davies–Bouldin Index

Optional:

- Calinski–Harabasz Score

Analysis:

- Cluster separation
- Error analysis

---

# Main Features

## Upload Dataset
Supported:
- CSV
- Excel

## Dataset Validation

Checks:

- Missing columns
- Invalid values

## Run Detection

User selects:

- K-Means
- DBSCAN

## Visualization

Display:

- Clusters
- Anomaly percentage
- Statistics

## Export Results

Export:

- CSV
- PDF

---

# Demo

Application Type:

Web Application

Technology:

Streamlit

---

# Technology Stack

Frontend:
- Streamlit

Backend:
- Python

Machine Learning:
- Scikit-learn

Data:
- Pandas
- NumPy

Visualization:
- Plotly

Storage:
- SQLite

---

# Project Structure

project/

├── data/

│   ├── raw/

│   └── processed/

│

├── notebooks/

│

├── src/

│   ├── data/

│   ├── models/

│   ├── evaluation/

│   └── app/

│

├── models/

│

├── requirements.txt

└── README.md

---

# Deliverables

- Source code
- Dataset or dataset link
- Trained model
- Report PDF
- Screenshots
- README

---

# Team Workflow

Member 1:
- Data + ML

Member 2:
- App + Visualization

Git workflow:

main

↓

dev

↓

feature branches

---

# Future Improvements

- Real-time monitoring
- Live packet capture
- REST API
- Docker deployment
