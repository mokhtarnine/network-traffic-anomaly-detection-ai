import pandas as pd
from pathlib import Path 

BASE_DIR = Path(__file__).resolve().parents[2]

TRAIN_PATH = BASE_DIR / "data" / "raw" / "KDDTrain+.txt"
TEST_PATH = BASE_DIR / "data" / "raw" / "KDDTest+.txt"

def load_nsl_kdd():
    if not TRAIN_PATH.exists():
        raise FileNotFoundError(f"Training dataset not found: {TRAIN_PATH}")
    
    if not TEST_PATH.exists():
        raise FileNotFoundError(f"Testing dataset not found: {TEST_PATH}")
    
    train_df = pd.read_csv(TRAIN_PATH, header=None)
    test_df = pd.read_csv(TEST_PATH, header=None)

    return train_df, test_df

if __name__ == "__main__":
    train_df , test_df = load_nsl_kdd()

    print("Datasets loaded successfully")
    print("Train shape:", train_df.shape)
    print("Test shape:", test_df.shape)
    print(train_df.head())