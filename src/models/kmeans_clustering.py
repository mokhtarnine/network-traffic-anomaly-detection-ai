from pathlib import Path
import sys
import joblib

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from sklearn.cluster import KMeans

from src.data.load_dataset import load_nsl_kdd
from src.data.preprocessing import prepare_clustering_data
from src.evaluation.metrics import evaluate_clustering, cluster_label_table


def print_section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def main():
    train_df, test_df = load_nsl_kdd()

    X_train_processed, X_test_processed, y_train, y_test, preprocessor = prepare_clustering_data(
        train_df,
        test_df,
    )

    print_section("Preprocessed Data Shape")
    print("X_train_processed:", X_train_processed.shape)
    print("X_test_processed:", X_test_processed.shape)

    kmeans = KMeans(
        n_clusters=5,
        random_state=42,
        n_init=10,
    )

    train_clusters = kmeans.fit_predict(X_train_processed)
    test_clusters = kmeans.predict(X_test_processed)
    #saving model .pk1 
    MODEL_DIR = PROJECT_ROOT / "models"
    MODEL_DIR.mkdir(exist_ok=True)

    joblib.dump(kmeans, MODEL_DIR / "kmeans_model.pkl")
    joblib.dump(preprocessor, MODEL_DIR / "preprocessor.pkl")

    print_section("Model Saved")
    print("K-Means model saved to:", MODEL_DIR / "kmeans_model.pkl")
    print("Preprocessor saved to:", MODEL_DIR / "preprocessor.pkl")

    #################################################################
    print_section("Train Cluster Counts")
    print(pd.Series(train_clusters).value_counts().sort_index())

    print_section("Test Cluster Counts")
    print(pd.Series(test_clusters).value_counts().sort_index())

    train_metrics = evaluate_clustering(
        X_train_processed,
        train_clusters,
        y_train,
    )

    print_section("Train Clustering Evaluation Metrics")
    for metric_name, metric_value in train_metrics.items():
        print(f"{metric_name}: {metric_value}")

    train_binary_table, train_original_table = cluster_label_table(
        train_clusters,
        y_train,
    )

    test_binary_table, test_original_table = cluster_label_table(
        test_clusters,
        y_test,
    )

    print_section("Train Cluster vs Binary Label")
    print(train_binary_table)

    print_section("Test Cluster vs Binary Label")
    print(test_binary_table)

    print_section("Train Cluster vs Original Label")
    print(train_original_table)

    print_section("Test Cluster vs Original Label")
    print(test_original_table)

    print_section("K-Means Summary")
    print("K-Means clustering completed with 5 clusters.")
    print("Labels were used only after clustering to understand the cluster contents.")
    print("Evaluation metrics were calculated after clustering, not during training.")


if __name__ == "__main__":
    main()