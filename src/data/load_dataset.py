import pandas as pd
from pathlib import Path 

BASE_DIR = Path(__file__).resolve().parents[2]

TRAIN_PATH = BASE_DIR / "data" / "raw" / "KDDTrain+.txt"
TEST_PATH = BASE_DIR / "data" / "raw" / "KDDTest+.txt"

NSL_KDD_COLUMNS = [
    "duration",
    "protocol_type",
    "service",
    "flag",
    "src_bytes",
    "dst_bytes",
    "land",
    "wrong_fragment",
    "urgent",
    "hot",
    "num_failed_logins",
    "logged_in",
    "num_compromised",
    "root_shell",
    "su_attempted",
    "num_root",
    "num_file_creations",
    "num_shells",
    "num_access_files",
    "num_outbound_cmds",
    "is_host_login",
    "is_guest_login",
    "count",
    "srv_count",
    "serror_rate",
    "srv_serror_rate",
    "rerror_rate",
    "srv_rerror_rate",
    "same_srv_rate",
    "diff_srv_rate",
    "srv_diff_host_rate",
    "dst_host_count",
    "dst_host_srv_count",
    "dst_host_same_srv_rate",
    "dst_host_diff_srv_rate",
    "dst_host_same_src_port_rate",
    "dst_host_srv_diff_host_rate",
    "dst_host_serror_rate",
    "dst_host_srv_serror_rate",
    "dst_host_rerror_rate",
    "dst_host_srv_rerror_rate",
    "label",
    "difficulty",
]

def load_nsl_kdd():
    if not TRAIN_PATH.exists():
        raise FileNotFoundError(f"Training dataset not found: {TRAIN_PATH}")
    
    if not TEST_PATH.exists():
        raise FileNotFoundError(f"Testing dataset not found: {TEST_PATH}")
    
    train_df = pd.read_csv(TRAIN_PATH, names=NSL_KDD_COLUMNS)
    test_df = pd.read_csv(TEST_PATH, names=NSL_KDD_COLUMNS)

    return train_df, test_df

if __name__ == "__main__":
    train_df , test_df = load_nsl_kdd()

    print("Datasets loaded successfully")
    print("Train shape:", train_df.shape)
    print("Test shape:", test_df.shape)
    print(train_df.head())

