import json
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).resolve().parents[2] / "analysis_history.db"


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                filename TEXT,
                algorithm TEXT,
                n_records INTEGER,
                n_anomalies INTEGER,
                anomaly_ratio REAL,
                silhouette_score REAL,
                davies_bouldin_score REAL,
                params_json TEXT
            )
        """)


def save_analysis(
    filename: str,
    algorithm: str,
    n_records: int,
    n_anomalies: int,
    metrics: dict,
    params: dict,
) -> int:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            """INSERT INTO analyses
               (timestamp, filename, algorithm, n_records, n_anomalies,
                anomaly_ratio, silhouette_score, davies_bouldin_score, params_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                datetime.now().isoformat(timespec="seconds"),
                filename,
                algorithm,
                n_records,
                n_anomalies,
                round(n_anomalies / n_records, 4) if n_records else 0.0,
                metrics.get("silhouette_score"),
                metrics.get("davies_bouldin_score"),
                json.dumps(params),
            ),
        )
        return cur.lastrowid


def get_history(limit: int = 20) -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(
            "SELECT * FROM analyses ORDER BY timestamp DESC LIMIT ?",
            conn,
            params=(limit,),
        )


def delete_analysis(row_id: int) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM analyses WHERE id = ?", (row_id,))
