import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _make_nslkdd_df(n: int = 200, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n_normal = n // 2
    n_neptune = n // 4
    n_smurf = n - n_normal - n_neptune
    labels = ["normal"] * n_normal + ["neptune"] * n_neptune + ["smurf"] * n_smurf

    return pd.DataFrame({
        "duration":                    rng.integers(0, 1000, n),
        "protocol_type":               rng.choice(["tcp", "udp", "icmp"], n),
        "service":                     rng.choice(["http", "ftp", "smtp", "ssh", "dns"], n),
        "flag":                        rng.choice(["SF", "S0", "REJ", "RSTO"], n),
        "src_bytes":                   rng.integers(0, 100_000, n),
        "dst_bytes":                   rng.integers(0, 100_000, n),
        "land":                        rng.integers(0, 2, n),
        "wrong_fragment":              rng.integers(0, 3, n),
        "urgent":                      rng.integers(0, 2, n),
        "hot":                         rng.integers(0, 30, n),
        "num_failed_logins":           rng.integers(0, 5, n),
        "logged_in":                   rng.integers(0, 2, n),
        "num_compromised":             rng.integers(0, 10, n),
        "root_shell":                  rng.integers(0, 2, n),
        "su_attempted":                rng.integers(0, 2, n),
        "num_root":                    rng.integers(0, 10, n),
        "num_file_creations":          rng.integers(0, 5, n),
        "num_shells":                  rng.integers(0, 2, n),
        "num_access_files":            rng.integers(0, 5, n),
        "num_outbound_cmds":           np.zeros(n, dtype=int),
        "is_host_login":               rng.integers(0, 2, n),
        "is_guest_login":              rng.integers(0, 2, n),
        "count":                       rng.integers(0, 511, n),
        "srv_count":                   rng.integers(0, 511, n),
        "serror_rate":                 rng.random(n),
        "srv_serror_rate":             rng.random(n),
        "rerror_rate":                 rng.random(n),
        "srv_rerror_rate":             rng.random(n),
        "same_srv_rate":               rng.random(n),
        "diff_srv_rate":               rng.random(n),
        "srv_diff_host_rate":          rng.random(n),
        "dst_host_count":              rng.integers(0, 255, n),
        "dst_host_srv_count":          rng.integers(0, 255, n),
        "dst_host_same_srv_rate":      rng.random(n),
        "dst_host_diff_srv_rate":      rng.random(n),
        "dst_host_same_src_port_rate": rng.random(n),
        "dst_host_srv_diff_host_rate": rng.random(n),
        "dst_host_serror_rate":        rng.random(n),
        "dst_host_srv_serror_rate":    rng.random(n),
        "dst_host_rerror_rate":        rng.random(n),
        "dst_host_srv_rerror_rate":    rng.random(n),
        "label":                       labels,
        "difficulty":                  rng.integers(0, 21, n),
    })


@pytest.fixture
def nslkdd_df():
    return _make_nslkdd_df()


@pytest.fixture
def small_X():
    rng = np.random.default_rng(42)
    return np.vstack([
        rng.normal([0, 0], 0.3, (40, 2)),
        rng.normal([5, 5], 0.3, (40, 2)),
    ])


@pytest.fixture
def clean_clusters():
    rng = np.random.default_rng(0)
    X = np.vstack([
        rng.normal([0, 0], 0.5, (50, 2)),
        rng.normal([5, 5], 0.5, (50, 2)),
    ])
    clusters = np.array([0] * 50 + [1] * 50)
    labels = pd.Series(["normal"] * 50 + ["neptune"] * 50)
    return X, clusters, labels
