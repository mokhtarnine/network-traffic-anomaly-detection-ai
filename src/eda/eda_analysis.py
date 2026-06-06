from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

import matplotlib.pyplot as plt

from src.data.load_dataset import load_nsl_kdd

def print_section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

def main():
    train_df, test_df = load_nsl_kdd()

    print_section("Dataset Shape")
    print("Train shape:", train_df.shape)
    print("Test shape:", test_df.shape)

    print_section("First 5 Rows")
    print(train_df.head())

    print_section("Column Names")
    print(train_df.columns.tolist())

    print_section("Dataset Info")
    print(train_df.info())

    print_section("Missing Values")
    print(train_df.isnull().sum())

    print_section("Duplicate Rows")
    print("Train duplicates:", train_df.duplicated().sum())
    print("Test duplicates:", test_df.duplicated().sum())

    print_section("Label Distribution")
    print(train_df["label"].value_counts())

    train_df["binary_label"] = train_df["label"].apply(
        lambda label: "normal" if label == "normal" else "attack"
    )

    test_df["binary_label"] = test_df["label"].apply(
        lambda label: "normal" if label == "normal" else "attack"
    )

    print_section("Binary Label Distribution")
    print(train_df["binary_label"].value_counts())

    print_section("Categorical Feature Distribution")
    categorical_columns = ["protocol_type", "service", "flag"]

    for column in categorical_columns:
        print(f"\n{column}:")
        print(train_df[column].value_counts().head(10))

    print_section("Numerical Summary")
    print(train_df.describe())

    print_section("Top 10 Attack Types")
    attack_counts = train_df[train_df["label"] != "normal"]["label"].value_counts()
    print(attack_counts.head(10))

    print_section("EDA Summary")
    print("Train and test datasets loaded successfully.")
    print("The dataset contains both normal and attack traffic.")
    print("The label column contains multiple attack types.")
    print("A binary_label column was created: normal vs attack.")
    print("Categorical columns need encoding before model training.")
    print("Numerical columns may need scaling before some models.")


if __name__ == "__main__":
    main()