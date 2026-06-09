import numpy as np
import pytest
from src.models.kmeans_model import train_kmeans, predict_kmeans, get_anomaly_mask
from src.models.dbscan_model import (
    train_dbscan, get_dbscan_clusters, get_anomaly_mask_dbscan, get_dbscan_summary,
)


# ── K-Means ───────────────────────────────────────────────────────────────────

def test_kmeans_returns_fitted_model(small_X):
    model = train_kmeans(small_X, n_clusters=2)
    assert hasattr(model, "labels_")
    assert model.n_clusters == 2


def test_kmeans_predict_shape(small_X):
    model = train_kmeans(small_X, n_clusters=2)
    preds = predict_kmeans(model, small_X)
    assert preds.shape == (len(small_X),)


def test_kmeans_predict_valid_labels(small_X):
    model = train_kmeans(small_X, n_clusters=2)
    preds = predict_kmeans(model, small_X)
    assert set(preds).issubset({0, 1})


def test_kmeans_separates_two_clusters(small_X):
    # Two well-separated blobs → silhouette should be high
    from sklearn.metrics import silhouette_score
    model = train_kmeans(small_X, n_clusters=2)
    preds = predict_kmeans(model, small_X)
    score = silhouette_score(small_X, preds)
    assert score > 0.7


def test_get_anomaly_mask_dtype(small_X):
    model = train_kmeans(small_X, n_clusters=2)
    preds = predict_kmeans(model, small_X)
    mask = get_anomaly_mask(preds, 0)
    assert mask.dtype == bool


def test_get_anomaly_mask_count(small_X):
    model = train_kmeans(small_X, n_clusters=2)
    preds = predict_kmeans(model, small_X)
    mask = get_anomaly_mask(preds, 0)
    assert mask.sum() == (preds == 0).sum()


# ── DBSCAN ────────────────────────────────────────────────────────────────────

def test_dbscan_returns_fitted_model(small_X):
    model = train_dbscan(small_X, eps=1.0, min_samples=3)
    clusters = get_dbscan_clusters(model)
    assert clusters.shape == (len(small_X),)


def test_dbscan_finds_clusters(small_X):
    model = train_dbscan(small_X, eps=1.0, min_samples=3)
    clusters = get_dbscan_clusters(model)
    summary = get_dbscan_summary(clusters)
    assert summary["n_clusters"] >= 1


def test_dbscan_summary_keys(small_X):
    model = train_dbscan(small_X, eps=1.0, min_samples=3)
    clusters = get_dbscan_clusters(model)
    summary = get_dbscan_summary(clusters)
    assert "n_clusters" in summary
    assert "n_noise_points" in summary
    assert "noise_ratio" in summary


def test_dbscan_noise_ratio_range(small_X):
    model = train_dbscan(small_X, eps=1.0, min_samples=3)
    clusters = get_dbscan_clusters(model)
    summary = get_dbscan_summary(clusters)
    assert 0.0 <= summary["noise_ratio"] <= 1.0


def test_get_anomaly_mask_dbscan_marks_noise():
    clusters = np.array([-1, 0, 1, -1, 0])
    mask = get_anomaly_mask_dbscan(clusters)
    assert list(mask) == [True, False, False, True, False]


def test_get_anomaly_mask_dbscan_all_noise():
    clusters = np.full(10, -1)
    mask = get_anomaly_mask_dbscan(clusters)
    assert mask.all()


def test_get_anomaly_mask_dbscan_no_noise():
    clusters = np.array([0, 1, 0, 1])
    mask = get_anomaly_mask_dbscan(clusters)
    assert not mask.any()
