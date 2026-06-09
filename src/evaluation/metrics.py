import numpy as np
import pandas as pd
from sklearn.metrics import silhouette_score, davies_bouldin_score, adjusted_rand_score


def create_binary_labels(labels: pd.Series) -> pd.Series:
    return labels.apply(
        lambda x: "normal" if str(x).strip().lower() == "normal" else "attack"
    )


def evaluate_clustering(
    X_processed: np.ndarray,
    clusters: np.ndarray,
    true_labels: pd.Series | None = None,
) -> dict:
    unique_clusters = np.unique(clusters[clusters != -1])
    result = {}

    if len(unique_clusters) >= 2:
        mask = clusters != -1
        X_eval = X_processed[mask] if not mask.all() else X_processed
        c_eval = clusters[mask] if not mask.all() else clusters
        n_sample = min(10000, len(X_eval))
        result["silhouette_score"] = round(
            silhouette_score(X_eval, c_eval, sample_size=n_sample, random_state=42), 4
        )
        result["davies_bouldin_score"] = round(davies_bouldin_score(X_eval, c_eval), 4)
    else:
        result["silhouette_score"] = None
        result["davies_bouldin_score"] = None

    if true_labels is not None:
        binary = create_binary_labels(true_labels)
        result["adjusted_rand_index"] = round(adjusted_rand_score(binary, clusters), 4)
    else:
        result["adjusted_rand_index"] = None

    return result


def cluster_label_table(
    clusters: np.ndarray,
    true_labels: pd.Series,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    binary = create_binary_labels(true_labels)
    df = pd.DataFrame({"cluster": clusters, "binary_label": binary, "label": true_labels})
    binary_table = pd.crosstab(df["cluster"], df["binary_label"])
    original_table = pd.crosstab(df["cluster"], df["label"])
    return binary_table, original_table


def identify_anomaly_cluster(binary_table: pd.DataFrame) -> int:
    if "attack" not in binary_table.columns:
        return int(binary_table.index[0])
    attack_ratio = binary_table["attack"] / (binary_table.sum(axis=1) + 1e-9)
    return int(attack_ratio.idxmax())


def error_analysis(
    clusters: np.ndarray,
    true_labels: pd.Series,
    anomaly_mask: np.ndarray,
) -> dict:
    binary = create_binary_labels(true_labels)
    df = pd.DataFrame({
        "cluster": clusters,
        "binary_label": binary,
        "label": true_labels,
        "flagged_anomaly": anomaly_mask,
    })

    # False negatives: attacks predicted as normal (not flagged)
    false_negatives = df[(df["binary_label"] == "attack") & (~df["flagged_anomaly"])]
    fn_by_type = false_negatives["label"].value_counts()

    # False positives: normal traffic flagged as anomaly
    false_positives = df[(df["binary_label"] == "normal") & df["flagged_anomaly"]]
    fp_count = len(false_positives)

    # True positives: attacks correctly flagged
    true_positives = df[(df["binary_label"] == "attack") & df["flagged_anomaly"]]
    tp_count = len(true_positives)

    total_attacks = int((binary == "attack").sum())
    total_normal = int((binary == "normal").sum())

    precision = tp_count / (tp_count + fp_count) if (tp_count + fp_count) > 0 else 0.0
    recall = tp_count / total_attacks if total_attacks > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    # Attack types per cluster
    attack_df = df[df["binary_label"] == "attack"]
    attack_type_per_cluster = (
        attack_df.groupby(["cluster", "label"])
        .size()
        .reset_index(name="count")
        .sort_values(["cluster", "count"], ascending=[True, False])
    )

    return {
        "total_attacks": total_attacks,
        "total_normal": total_normal,
        "true_positives": tp_count,
        "false_positives": fp_count,
        "false_negatives": len(false_negatives),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "missed_attack_types": fn_by_type,
        "attack_type_per_cluster": attack_type_per_cluster,
    }
