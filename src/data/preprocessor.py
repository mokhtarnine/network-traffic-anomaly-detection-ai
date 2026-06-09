import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

CATEGORICAL_COLUMNS = ["protocol_type", "service", "flag"]
DROP_COLUMNS = ["label", "difficulty", "binary_label"]
PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"


def _get_feature_cols(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    cat = [c for c in CATEGORICAL_COLUMNS if c in df.columns]
    num = [c for c in df.columns if c not in CATEGORICAL_COLUMNS and c not in DROP_COLUMNS]
    return cat, num


def fit_and_transform(
    df: pd.DataFrame,
    drop_label_cols: bool = True,
) -> tuple[np.ndarray, ColumnTransformer, pd.Series | None]:
    labels = df["label"].copy() if "label" in df.columns else None
    cols_to_drop = [c for c in DROP_COLUMNS if c in df.columns] if drop_label_cols else []
    X = df.drop(columns=cols_to_drop)
    cat, num = _get_feature_cols(X)

    preprocessor = ColumnTransformer(
        transformers=[
            ("categorical", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat),
            ("numerical", StandardScaler(), num),
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


def save_processed(
    X: np.ndarray,
    labels: pd.Series | None,
    preprocessor: ColumnTransformer,
    split: str = "train",
) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    np.save(PROCESSED_DIR / f"X_{split}.npy", X)
    if labels is not None:
        labels.to_csv(PROCESSED_DIR / f"y_{split}.csv", index=False)
    joblib.dump(preprocessor, PROCESSED_DIR / "preprocessor.pkl")


def load_processed(split: str = "train") -> tuple[np.ndarray, pd.Series | None]:
    X = np.load(PROCESSED_DIR / f"X_{split}.npy")
    label_path = PROCESSED_DIR / f"y_{split}.csv"
    labels = pd.read_csv(label_path).squeeze() if label_path.exists() else None
    return X, labels
