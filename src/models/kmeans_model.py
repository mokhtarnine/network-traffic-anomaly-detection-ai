import numpy as np
import joblib
from pathlib import Path
from sklearn.cluster import KMeans

MODELS_DIR = Path(__file__).resolve().parents[2] / "models"


def train_kmeans(X: np.ndarray, n_clusters: int = 5, random_state: int = 42) -> KMeans:
    model = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    model.fit(X)
    return model


def predict_kmeans(model: KMeans, X: np.ndarray) -> np.ndarray:
    return model.predict(X)


def load_pretrained_kmeans(model_path: str | Path | None = None) -> KMeans:
    path = Path(model_path) if model_path else MODELS_DIR / "kmeans_model.pkl"
    return joblib.load(path)


def get_anomaly_mask(clusters: np.ndarray, anomaly_cluster_id: int) -> np.ndarray:
    return clusters == anomaly_cluster_id
