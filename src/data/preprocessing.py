from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
"""
in this part we work on cleaning and perpecess data for prepare for culters """

def prepare_clustering_data(train_df, test_df):
    drop_columns = ["label", "difficulty"]

    if "binary_label" in train_df.columns:
        drop_columns.append("binary_labael")

    y_train = train_df["label"]
    y_test = test_df["label"]

    x_train = train_df.drop(columns= drop_columns)
    x_test = test_df.drop(columns= drop_columns)

    categorical_columns = ["protocol_type", "service", "flag"]

    numerical_columns = [
        column for column in x_train.columns
        if column not in categorical_columns
    ]

    preprocessor = ColumnTransformer(
        transformers=[
            ("categorical", OneHotEncoder(handle_unknown="ignore"), categorical_columns),
            ("numerical", StandardScaler(), numerical_columns),
        ]
    )

    x_train_processed = preprocessor.fit_transform(x_train)
    x_test_processed = preprocessor.transform(x_test)

    return x_train_processed, x_test_processed , y_train , y_test, preprocessor

"""
# this part just test if clearn data work correct or not?
if __name__ == "__main__":
    from pathlib import Path
    import sys

    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(PROJECT_ROOT))

    from src.data.load_dataset import load_nsl_kdd

    train_df, test_df = load_nsl_kdd()

    X_train_processed, X_test_processed, y_train, y_test, preprocessor = prepare_clustering_data(
        train_df,
        test_df,
    )

    print("Preprocessing completed successfully")
    print("X_train_processed shape:", X_train_processed.shape)
    print("X_test_processed shape:", X_test_processed.shape)
    print("y_train shape:", y_train.shape)
    print("y_test shape:", y_test.shape)
    print("Processed data type:", type(X_train_processed))
    print("First 5 labels:")
    print(y_train.head())
    """