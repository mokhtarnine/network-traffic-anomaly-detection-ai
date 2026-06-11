import numpy as np
import pandas as pd
import pytest
from src.evaluation.metrics import (
    create_binary_labels,
    evaluate_clustering,
    identify_anomaly_cluster,
    cluster_label_table,
    error_analysis,
)


# ── create_binary_labels ──────────────────────────────────────────────────────

def test_binary_labels_normal():
    labels = pd.Series(["normal", "neptune", "NORMAL", "smurf"])
    binary = create_binary_labels(labels)
    assert list(binary) == ["normal", "attack", "normal", "attack"]


def test_binary_labels_all_normal():
    labels = pd.Series(["normal", "normal"])
    binary = create_binary_labels(labels)
    assert all(b == "normal" for b in binary)


# ── evaluate_clustering ───────────────────────────────────────────────────────

def test_evaluate_has_all_keys(clean_clusters):
    X, clusters, labels = clean_clusters
    result = evaluate_clustering(X, clusters, labels)
    assert "silhouette_score" in result
    assert "davies_bouldin_score" in result
    assert "adjusted_rand_index" in result


def test_silhouette_in_valid_range(clean_clusters):
    X, clusters, labels = clean_clusters
    result = evaluate_clustering(X, clusters, labels)
    assert -1.0 <= result["silhouette_score"] <= 1.0


def test_all_noise_returns_none():
    X = np.random.default_rng(0).random((30, 2))
    clusters = np.full(30, -1)
    result = evaluate_clustering(X, clusters)
    assert result["silhouette_score"] is None
    assert result["davies_bouldin_score"] is None


def test_no_labels_gives_none_ari(clean_clusters):
    X, clusters, _ = clean_clusters
    result = evaluate_clustering(X, clusters, true_labels=None)
    assert result["adjusted_rand_index"] is None


def test_single_cluster_returns_none():
    X = np.random.default_rng(1).random((20, 2))
    clusters = np.zeros(20, dtype=int)
    result = evaluate_clustering(X, clusters)
    assert result["silhouette_score"] is None


# ── identify_anomaly_cluster ──────────────────────────────────────────────────

def test_identifies_highest_attack_ratio():
    binary_table = pd.DataFrame(
        {"attack": [10, 90, 5], "normal": [90, 10, 50]},
        index=[0, 1, 2],
    )
    assert identify_anomaly_cluster(binary_table) == 1


def test_no_attack_column_returns_first():
    binary_table = pd.DataFrame({"normal": [100, 50]}, index=[0, 1])
    result = identify_anomaly_cluster(binary_table)
    assert result == 0


# ── error_analysis ────────────────────────────────────────────────────────────

def test_perfect_detection():
    clusters = np.array([0, 0, 1, 1])
    labels = pd.Series(["normal", "normal", "neptune", "smurf"])
    anomaly_mask = np.array([False, False, True, True])
    err = error_analysis(clusters, labels, anomaly_mask)
    assert err["precision"] == 1.0
    assert err["recall"] == 1.0
    assert err["f1_score"] == 1.0
    assert err["false_negatives"] == 0


def test_zero_detection():
    clusters = np.array([0, 0, 0, 0])
    labels = pd.Series(["normal", "normal", "neptune", "smurf"])
    anomaly_mask = np.array([False, False, False, False])
    err = error_analysis(clusters, labels, anomaly_mask)
    assert err["recall"] == 0.0
    assert err["precision"] == 0.0
    assert err["false_negatives"] == 2


def test_missed_attack_types_populated():
    clusters = np.array([0, 0, 0, 0])
    labels = pd.Series(["normal", "neptune", "smurf", "neptune"])
    anomaly_mask = np.array([False, False, False, False])
    err = error_analysis(clusters, labels, anomaly_mask)
    assert "neptune" in err["missed_attack_types"].index


def test_error_analysis_keys():
    clusters = np.array([0, 1])
    labels = pd.Series(["normal", "neptune"])
    mask = np.array([False, True])
    err = error_analysis(clusters, labels, mask)
    for key in ("precision", "recall", "f1_score", "false_negatives",
                "missed_attack_types", "attack_type_per_cluster"):
        assert key in err


# ── cluster_label_table ───────────────────────────────────────────────────────

def test_cluster_label_table_shape():
    clusters = np.array([0, 0, 1, 1])
    labels = pd.Series(["normal", "neptune", "smurf", "normal"])
    binary_table, orig_table = cluster_label_table(clusters, labels)
    assert set(binary_table.index) == {0, 1}
    assert "attack" in binary_table.columns or "normal" in binary_table.columns
