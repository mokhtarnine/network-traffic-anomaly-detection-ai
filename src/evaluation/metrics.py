import numpy as np
import pandas as pd
from sklearn.metrics import silhouette_score, davies_bouldin_score, adjusted_rand_score


def create_binary_labels(labels: pd.Series) -> pd.Series:
    return labels.apply(
        lambda label: "normal" if str(label).strip().lower() == "normal" else "attack"
    )


def evaluate_clustering(
    X_processed: np.ndarray,
    clusters: np.ndarray,
    true_labels: pd.Series | None = None,
) -> dict:
    unique_clusters = np.unique(clusters[clusters != -1])
    result = {}

    if len(unique_clusters) >= 2:
        # Use only non-noise points for silhouette/DB when DBSCAN labels -1
        mask = clusters != -1
        X_eval = X_processed[mask] if mask.any() and not mask.all() else X_processed
        c_eval = clusters[mask] if mask.any() and not mask.all() else clusters

        n_sample = min(10000, len(X_eval))
        result["silhouette_score"] = round(
            silhouette_score(X_eval, c_eval, sample_size=n_sample, random_state=42), 4
        )
        result["davies_bouldin_score"] = round(davies_bouldin_score(X_eval, c_eval), 4)
    else:
        result["silhouette_score"] = None
        result["davies_bouldin_score"] = None

    if true_labels is not None:
        binary_labels = create_binary_labels(true_labels)
        result["adjusted_rand_index"] = round(adjusted_rand_score(binary_labels, clusters), 4)
    else:
        result["adjusted_rand_index"] = None

    return result


def cluster_label_table(
    clusters: np.ndarray,
    true_labels: pd.Series,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    binary_labels = create_binary_labels(true_labels)

    results = pd.DataFrame({
        "cluster": clusters,
        "binary_label": binary_labels,
        "label": true_labels,
    })

    binary_table = pd.crosstab(results["cluster"], results["binary_label"])
    original_label_table = pd.crosstab(results["cluster"], results["label"])

    return binary_table, original_label_table


def identify_anomaly_cluster(binary_table: pd.DataFrame) -> int:
    if "attack" not in binary_table.columns:
        return int(binary_table.index[0])

    attack_ratio = binary_table["attack"] / (binary_table.sum(axis=1) + 1e-9)
    return int(attack_ratio.idxmax())
