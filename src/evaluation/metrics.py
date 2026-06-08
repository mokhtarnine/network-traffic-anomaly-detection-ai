import pandas as pd
from sklearn.metrics import silhouette_score, davies_bouldin_score, adjusted_rand_score
""" eveluatoin k-Means for choice best k , number of cluster"""

#convert all attacks into one category
def create_binary_labels(labels):
    return labels.apply(
        lambda label: "normal" if str(label).strip().lower() == "normal" else "attack"
    )

def evaluate_clustering(X_processed, clusters, true_labels):
    binary_labels = create_binary_labels(true_labels)

    silhouette = silhouette_score(
        X_processed,
        clusters,
        sample_size=10000,
        random_state=42,
    )

    davies_bouldin = davies_bouldin_score(X_processed, clusters)
    adjusted_rand = adjusted_rand_score(binary_labels, clusters)

    return {
        "silhouette_score": silhouette,
        "davies_bouldin_score": davies_bouldin,
        "adjusted_rand_index": adjusted_rand,
    }

#create analysis tables 
def cluster_label_table(clusters, true_labels):
    binary_labels = create_binary_labels(true_labels)

    results = pd.DataFrame({
        "cluster": clusters,
        "binary_label": binary_labels,
        "label": true_labels,
    })

    binary_table = pd.crosstab(results["cluster"], results["binary_label"])
    original_label_table = pd.crosstab(results["cluster"], results["label"])

    return binary_table, original_label_table