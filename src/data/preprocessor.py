import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

CATEGORICAL_COLUMNS = ["protocol_type", "service", "flag"]
DROP_COLUMNS = ["label", "difficulty", "binary_label"]


def _get_numerical_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c not in CATEGORICAL_COLUMNS and c not in DROP_COLUMNS]


def fit_and_transform(
    df: pd.DataFrame,
    drop_label_cols: bool = True,
) -> tuple[np.ndarray, ColumnTransformer, pd.Series | None]:
    labels = df["label"].copy() if "label" in df.columns else None

    cols_to_drop = [c for c in DROP_COLUMNS if c in df.columns] if drop_label_cols else []
    X = df.drop(columns=cols_to_drop)

    cat_present = [c for c in CATEGORICAL_COLUMNS if c in X.columns]
    num_cols = [c for c in X.columns if c not in CATEGORICAL_COLUMNS]

    preprocessor = ColumnTransformer(
        transformers=[
            ("categorical", OneHotEncoder(handle_unknown="ignore"), cat_present),
            ("numerical", StandardScaler(), num_cols),
        ]
    )

    X_processed = preprocessor.fit_transform(X)
    return X_processed, preprocessor, labels


def transform_with_existing(
    df: pd.DataFrame,
    fitted_preprocessor: ColumnTransformer,
) -> np.ndarray:
    cols_to_drop = [c for c in DROP_COLUMNS if c in df.columns]
    X = df.drop(columns=cols_to_drop)
    return fitted_preprocessor.transform(X)


def get_feature_names(fitted_preprocessor: ColumnTransformer) -> list[str]:
    names = []
    for name, transformer, cols in fitted_preprocessor.transformers_:
        if name == "categorical" and hasattr(transformer, "get_feature_names_out"):
            names.extend(transformer.get_feature_names_out(cols).tolist())
        else:
            names.extend(cols if isinstance(cols, list) else list(cols))
    return names
