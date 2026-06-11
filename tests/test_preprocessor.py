import numpy as np
import pytest
from src.data.preprocessor import fit_and_transform, get_feature_names, transform_with_existing


def test_output_is_ndarray(nslkdd_df):
    X, _, _ = fit_and_transform(nslkdd_df)
    assert isinstance(X, np.ndarray)


def test_row_count_preserved(nslkdd_df):
    X, _, _ = fit_and_transform(nslkdd_df)
    assert X.shape[0] == len(nslkdd_df)


def test_onehot_expands_columns(nslkdd_df):
    X, _, _ = fit_and_transform(nslkdd_df)
    # 41 raw features → OneHot expands 3 categoricals → must have more than 41 cols
    assert X.shape[1] > 41


def test_no_nan_after_transform(nslkdd_df):
    X, _, _ = fit_and_transform(nslkdd_df)
    assert not np.isnan(X).any()


def test_labels_preserved(nslkdd_df):
    _, _, labels = fit_and_transform(nslkdd_df)
    assert labels is not None
    assert list(labels) == list(nslkdd_df["label"])


def test_feature_names_match_columns(nslkdd_df):
    X, preprocessor, _ = fit_and_transform(nslkdd_df)
    names = get_feature_names(preprocessor)
    assert len(names) == X.shape[1]


def test_transform_with_existing_shape(nslkdd_df):
    X_train, preprocessor, _ = fit_and_transform(nslkdd_df)
    X_test = transform_with_existing(nslkdd_df, preprocessor)
    assert X_test.shape == X_train.shape


def test_label_column_dropped(nslkdd_df):
    # After fit_and_transform, "label" must not appear as a feature
    X, preprocessor, _ = fit_and_transform(nslkdd_df)
    names = get_feature_names(preprocessor)
    assert "label" not in names
    assert "difficulty" not in names
