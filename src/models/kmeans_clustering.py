from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from sklearn.cluster import KMeans

from src.data.load_dataset import load_nsl_kdd
from src.data.preprocessing import prepare_clustering_data

def print_section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

def main():
    train_df, test_df = load_nsl_kdd()

    x_train_processed, x_test_processed, y_train, y_test, preprocessor = prepare_clustering_data(
        train_df,
        test_df
    )

    print_section("Preprocessed Data Shape")
    print("X_train_processed:", x_train_processed.shape)
    print("X_test_processed:",x_test_processed.shape)
    # create Kmeans model
    kmeans = KMeans(
        n_clusters=2,
        random_state=42,
        n_init=10,
    )

    train_clusters = kmeans.fit_predict(x_train_processed)
    test_clusters = kmeans.predict(x_test_processed)

    print_section("Train Cluster Counts")
    print(pd.Series(train_clusters).value_counts().sort_index())

    print_section("Test Cluster Counts")
    print(pd.Series(test_clusters).value_counts().sort_index())

    train_results = pd.DataFrame({
        "label": y_train,
        "cluster": train_clusters,
    })
    test_results = pd.DataFrame({
        "label": y_test,
        "cluster": test_clusters,
    })

    train_results["binary_label"] = train_results["label"].apply(
    lambda label: "normal" if str(label).strip().lower() == "normal" else "attack"
    )

    test_results["binary_label"] = test_results["label"].apply(
        lambda label: "normal" if str(label).strip().lower() == "normal" else "attack"
    )
    print_section("Train cluster vs Binary Label")
    print(pd.crosstab(train_results["cluster"], train_results["binary_label"]))

    print_section("Test cluster vs Binary Label")
    print(pd.crosstab(test_results["cluster"], test_results["binary_label"]))

    print_section("Train cluster vs Original Label")
    print(pd.crosstab(train_results["cluster"], train_results["label"]))

    print_section("Train Label Check")
    print(y_train.value_counts().head())
    print(y_train.unique()[:10])

    ("K-Means Summary")
    print("K-Means clustering completed with 2 clusters.")
    print("Labels were used only after clustering to understand the cluster contents.")
    print("If one cluster contains mostly normal records and the other mostly attacks, the clustering is useful.")


if __name__ == "__main__":
    main()