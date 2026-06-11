import io
import pandas as pd
import pytest
from src.data.loader import validate_dataframe, get_dataset_summary


# ── validate_dataframe ────────────────────────────────────────────────────────

def test_validate_empty_dataframe():
    ok, msg = validate_dataframe(pd.DataFrame())
    assert not ok
    assert "empty" in msg.lower()


def test_validate_too_few_columns():
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    ok, msg = validate_dataframe(df)
    assert not ok
    assert "few" in msg.lower()


def test_validate_entirely_null_column():
    df = pd.DataFrame({f"col_{i}": [1, 2, 3] for i in range(6)})
    df["all_null"] = None
    ok, msg = validate_dataframe(df)
    assert not ok
    assert "null" in msg.lower()


def test_validate_valid_nslkdd(nslkdd_df):
    ok, msg = validate_dataframe(nslkdd_df)
    assert ok
    assert "valid" in msg.lower()


# ── get_dataset_summary ───────────────────────────────────────────────────────

def test_summary_row_count(nslkdd_df):
    summary = get_dataset_summary(nslkdd_df)
    assert summary["n_rows"] == len(nslkdd_df)


def test_summary_col_count(nslkdd_df):
    summary = get_dataset_summary(nslkdd_df)
    assert summary["n_cols"] == nslkdd_df.shape[1]


def test_summary_null_count_clean(nslkdd_df):
    summary = get_dataset_summary(nslkdd_df)
    assert summary["null_count"] == 0


def test_summary_detects_label_column(nslkdd_df):
    summary = get_dataset_summary(nslkdd_df)
    assert summary["has_label"] is True


def test_summary_no_label_column():
    df = pd.DataFrame({"a": [1], "b": [2], "c": [3], "d": [4], "e": [5]})
    summary = get_dataset_summary(df)
    assert summary["has_label"] is False
