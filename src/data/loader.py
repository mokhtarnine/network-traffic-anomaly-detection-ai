import pandas as pd

NSL_KDD_COLUMNS = [
    "duration", "protocol_type", "service", "flag", "src_bytes", "dst_bytes",
    "land", "wrong_fragment", "urgent", "hot", "num_failed_logins", "logged_in",
    "num_compromised", "root_shell", "su_attempted", "num_root", "num_file_creations",
    "num_shells", "num_access_files", "num_outbound_cmds", "is_host_login",
    "is_guest_login", "count", "srv_count", "serror_rate", "srv_serror_rate",
    "rerror_rate", "srv_rerror_rate", "same_srv_rate", "diff_srv_rate",
    "srv_diff_host_rate", "dst_host_count", "dst_host_srv_count",
    "dst_host_same_srv_rate", "dst_host_diff_srv_rate", "dst_host_same_src_port_rate",
    "dst_host_srv_diff_host_rate", "dst_host_serror_rate", "dst_host_srv_serror_rate",
    "dst_host_rerror_rate", "dst_host_srv_rerror_rate", "label", "difficulty",
]

REQUIRED_CATEGORICAL = ["protocol_type", "service", "flag"]


def load_from_upload(uploaded_file) -> pd.DataFrame:
    ext = uploaded_file.name.rsplit(".", 1)[-1].lower()
    uploaded_file.seek(0)

    if ext == "csv":
        return pd.read_csv(uploaded_file)
    elif ext == "xlsx":
        return pd.read_excel(uploaded_file, engine="openpyxl")
    elif ext == "xls":
        try:
            return pd.read_excel(uploaded_file)
        except ImportError:
            raise ValueError("Reading .xls files requires xlrd: pip install xlrd")
    elif ext == "txt":
        return pd.read_csv(uploaded_file, names=NSL_KDD_COLUMNS)
    else:
        raise ValueError(f"Unsupported file format '.{ext}'. Upload CSV, Excel, or NSL-KDD TXT.")


def validate_dataframe(df: pd.DataFrame) -> tuple[bool, str]:
    if df.empty:
        return False, "The uploaded file is empty."

    if df.shape[1] < 5:
        return False, f"Too few columns ({df.shape[1]}). Expected at least 5 feature columns."

    fully_null = [c for c in df.columns if df[c].isna().all()]
    if fully_null:
        return False, f"Columns are entirely null: {fully_null}"

    return True, "Dataset is valid."


def get_dataset_summary(df: pd.DataFrame) -> dict:
    return {
        "n_rows": len(df),
        "n_cols": df.shape[1],
        "null_count": int(df.isna().sum().sum()),
        "duplicate_count": int(df.duplicated().sum()),
        "column_names": list(df.columns),
        "has_label": "label" in df.columns,
    }
