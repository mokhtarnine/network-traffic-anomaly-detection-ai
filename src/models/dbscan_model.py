import numpy as np
from sklearn.cluster import DBSCAN


def train_dbscan(X: np.ndarray, eps: float = 2.0, min_samples: int = 10) -> DBSCAN:
    model = DBSCAN(eps=eps, min_samples=min_samples, n_jobs=-1)
    model.fit(X)
    return model


def get_dbscan_clusters(model: DBSCAN) -> np.ndarray:
    return model.labels_


def get_anomaly_mask_dbscan(clusters: np.ndarray) -> np.ndarray:
    return clusters == -1


def get_dbscan_summary(clusters: np.ndarray) -> dict:
    unique = np.unique(clusters)
    n_clusters = int((unique >= 0).sum())
    n_noise = int((clusters == -1).sum())
    return {
        "n_clusters": n_clusters,
        "n_noise_points": n_noise,
        "noise_ratio": round(n_noise / len(clusters), 4) if len(clusters) else 0.0,
    }
