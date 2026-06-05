import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "data" / "raw" / "KDDTrain+.txt"

def load_nsl_kdd():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH, header=None)
    return df

if __name__ == "__main__":
    df = load_nsl_kdd()
    print("Dataset loaded successfully")
    print("Shape:", df.shape)
    print(df.head())