# Web Application

## Application Overview

The application is a web-based interface that allows users to detect anomalous network traffic using clustering algorithms.

Users interact with the system through a simple browser interface without needing to execute Python scripts manually.

The application automates the complete analysis workflow from dataset upload to result visualization.

---

# How the Application Works

The application follows the process below:

Upload Dataset

↓

Validate Input File

↓

Run Data Preprocessing

↓

Execute Detection Algorithm

↓

Generate Clusters

↓

Identify Anomalies

↓

Display Results

↓

Export Report

---

# Application Workflow

## 1. Upload Dataset

The user uploads a network traffic dataset.

Supported formats:

- CSV
- Excel (.xlsx)
- TXT (NSL-KDD)

Example:

KDDTest+.txt

---

## 2. Dataset Validation

The application verifies:

- File integrity
- Required columns
- Empty values
- Supported format

If validation fails, an error message is displayed.

---

## 3. Data Preparation

The application automatically prepares the uploaded data.

Processing includes:

- Cleaning
- Encoding
- Scaling
- Feature preparation

---

## 4. Run Detection

The user selects the detection algorithm.

Available options:

- K-Means
- DBSCAN

The application executes the selected model.

---

## 5. Display Results

The system displays:

- Total analyzed records
- Number of detected anomalies
- Cluster distribution
- Evaluation metrics
- Graphical visualization

---

## 6. Export Results

Users can export:

- CSV report
- PDF report

---

# Technology Stack

## Frontend

Streamlit

Responsible for:

- User interface
- File upload
- Visualization
- Interaction

---

## Backend

Python

Responsible for:

- Application logic
- Data processing
- Communication between interface and models

---

## Machine Learning

Scikit-learn

Responsible for:

- K-Means
- DBSCAN
- Model execution

---

## Data Processing

Pandas

Responsible for:

- Dataset loading
- Cleaning
- Transformation

NumPy

Responsible for:

- Numerical operations

---

## Visualization

Plotly

Responsible for:

- Interactive charts
- Cluster visualization

---

## Storage

SQLite

Responsible for:

- Saving analysis history
- Export metadata

---

# Application Architecture

Browser

↓

Streamlit Interface

↓

Python Backend

↓

Preprocessing Pipeline

↓

Clustering Model

↓

Results Visualization

# N.b !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1
for this step push on branch of app
 
