import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from sklearn.decomposition import PCA

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.app.database import delete_analysis, get_history, init_db, save_analysis
from src.data.loader import get_dataset_summary, load_from_upload, validate_dataframe
from src.data.preprocessor import fit_and_transform, save_processed, transform_with_existing
from src.eda.eda_analysis import (
    fig_attack_types, fig_binary_pie, fig_categorical_distributions,
    fig_correlation_heatmap, fig_label_distribution, fig_numeric_distributions,
)
from src.evaluation.metrics import (
    cluster_label_table, error_analysis, evaluate_clustering, identify_anomaly_cluster,
)
from src.models.dbscan_model import (
    get_anomaly_mask_dbscan, get_dbscan_clusters, get_dbscan_summary, train_dbscan,
)
from src.models.kmeans_model import (
    get_anomaly_mask, load_pretrained_kmeans, predict_kmeans, train_kmeans,
)

# ── in-app chart layout ────────────────────────────────────────────────────────

_CHART = dict(
    template="plotly_white",
    font=dict(family="Inter, system-ui, -apple-system, sans-serif", size=12, color="#374151"),
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=40, r=20, t=50, b=40),
    hoverlabel=dict(bgcolor="white", font_size=12, bordercolor="#e2e8f0"),
    title_font=dict(size=14, color="#0f172a"),
)

_C_NORMAL  = "#4f86f7"
_C_ANOMALY = "#ef4444"

# ── cached figure wrappers ────────────────────────────────────────────────────

_fig_label_dist = st.cache_data(show_spinner=False)(fig_label_distribution)
_fig_binary_pie = st.cache_data(show_spinner=False)(fig_binary_pie)
_fig_cat_dists  = st.cache_data(show_spinner=False)(fig_categorical_distributions)
_fig_num_dists  = st.cache_data(show_spinner=False)(fig_numeric_distributions)
_fig_corr       = st.cache_data(show_spinner=False)(fig_correlation_heatmap)
_fig_attacks    = st.cache_data(show_spinner=False)(fig_attack_types)

# ── state helpers ─────────────────────────────────────────────────────────────

STATE_DOWNSTREAM = [
    "processed_X", "labels", "preprocessor",
    "clusters", "anomaly_mask", "metrics",
    "anomaly_cluster_id", "anomaly_purity",
]


def _clear_downstream() -> None:
    for key in STATE_DOWNSTREAM:
        st.session_state.pop(key, None)


@st.cache_data(show_spinner=False)
def _pca_2d(X: np.ndarray) -> np.ndarray:
    n = min(2, X.shape[1])
    return PCA(n_components=n, random_state=42).fit_transform(X)


# ── CSS injection ─────────────────────────────────────────────────────────────

def _inject_css() -> None:
    st.markdown("""
<style>
/* ── Metric cards ─────────────────────────────────────────────────────────── */
[data-testid="metric-container"] {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 16px 20px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,.05);
    transition: box-shadow .2s, transform .2s;
}
[data-testid="metric-container"]:hover {
    box-shadow: 0 4px 14px rgba(0,0,0,.09);
    transform: translateY(-1px);
}
[data-testid="stMetricLabel"] { color: #64748b !important; font-size: .8rem !important; font-weight: 600 !important; }
[data-testid="stMetricValue"] { color: #0f172a !important; font-size: 1.5rem !important; font-weight: 700 !important; }

/* ── Primary run buttons ──────────────────────────────────────────────────── */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: .88rem !important;
    transition: all .18s ease !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(37,99,235,.22) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* ── Download buttons ─────────────────────────────────────────────────────── */
.stDownloadButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: .88rem !important;
    background: #eff6ff !important;
    color: #1d4ed8 !important;
    border: 1px solid #bfdbfe !important;
    transition: all .18s ease !important;
}
.stDownloadButton > button:hover {
    background: #dbeafe !important;
    border-color: #93c5fd !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(37,99,235,.18) !important;
}

/* ── Tabs ─────────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px !important;
    background: #f1f5f9 !important;
    border-radius: 10px !important;
    padding: 4px !important;
    border-bottom: none !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 7px !important;
    padding: 6px 18px !important;
    font-weight: 500 !important;
    color: #64748b !important;
    background: transparent !important;
    transition: all .15s ease !important;
    border: none !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: white !important;
    color: #1e40af !important;
    font-weight: 700 !important;
    box-shadow: 0 1px 4px rgba(0,0,0,.10) !important;
}
.stTabs [data-baseweb="tab-highlight"] { display: none !important; }
.stTabs [data-baseweb="tab-border"]    { display: none !important; }

/* ── Expanders ────────────────────────────────────────────────────────────── */
[data-testid="stExpander"] {
    border-radius: 10px !important;
    border: 1px solid #e2e8f0 !important;
    overflow: hidden !important;
}
[data-testid="stExpander"] summary {
    font-weight: 600 !important;
}

/* ── File uploader ────────────────────────────────────────────────────────── */
[data-testid="stFileUploaderDropzone"] {
    border: 2px dashed #93c5fd !important;
    border-radius: 12px !important;
    background: #eff6ff !important;
    transition: all .2s ease !important;
}
[data-testid="stFileUploaderDropzone"]:hover {
    border-color: #3b82f6 !important;
    background: #dbeafe !important;
}

/* ── Sidebar ──────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    border-right: 1px solid #e2e8f0 !important;
    background: #fafafa !important;
}
[data-testid="stSidebar"] h1 {
    font-size: 1.1rem !important;
    color: #0f172a !important;
    font-weight: 700 !important;
}

/* ── Info / success / warning ─────────────────────────────────────────────── */
[data-testid="stAlert"] { border-radius: 10px !important; }

/* ── Section divider ──────────────────────────────────────────────────────── */
hr { border-color: #f1f5f9 !important; }

/* ── Main headers ─────────────────────────────────────────────────────────── */
h2 { color: #0f172a !important; font-weight: 700 !important; }
</style>
""", unsafe_allow_html=True)


# ── empty state ────────────────────────────────────────────────────────────────

def _render_empty_state() -> None:
    st.markdown("""
<div style="margin:2rem 0 1rem">
  <p style="color:#64748b;font-size:1rem;margin-bottom:1.8rem">
    Upload your NSL-KDD traffic dataset below and the app will guide you through
    every step automatically.
  </p>
  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:1.5rem">

    <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:12px;
                padding:22px 18px;display:flex;flex-direction:column;gap:8px">
      <span style="font-size:1.8rem">📂</span>
      <span style="font-weight:700;color:#1e40af;font-size:.95rem">1 · Upload &amp; EDA</span>
      <span style="color:#3b82f6;font-size:.82rem;line-height:1.4">
        Drag &amp; drop a CSV, Excel, or NSL-KDD .txt file.
        Automatic validation and exploratory analysis.
      </span>
    </div>

    <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:12px;
                padding:22px 18px;display:flex;flex-direction:column;gap:8px">
      <span style="font-size:1.8rem">🔍</span>
      <span style="font-weight:700;color:#166534;font-size:.95rem">2 · Detect</span>
      <span style="color:#16a34a;font-size:.82rem;line-height:1.4">
        Preprocessing pipeline + unsupervised clustering
        (K-Means or DBSCAN) to find anomalies.
      </span>
    </div>

    <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:12px;
                padding:22px 18px;display:flex;flex-direction:column;gap:8px">
      <span style="font-size:1.8rem">📄</span>
      <span style="font-weight:700;color:#92400e;font-size:.95rem">3 · Export</span>
      <span style="color:#d97706;font-size:.82rem;line-height:1.4">
        Download a flagged CSV or PDF report, and save
        results to the built-in history database.
      </span>
    </div>

  </div>
</div>
""", unsafe_allow_html=True)


# ── step progress ──────────────────────────────────────────────────────────────

def _step_badge(label: str, *, done: bool, active: bool) -> str:
    if done:
        bg, color, border, icon = "#dcfce7", "#16a34a", "#bbf7d0", "✓"
    elif active:
        bg, color, border, icon = "#dbeafe", "#2563eb", "#bfdbfe", "▶"
    else:
        bg, color, border, icon = "#f1f5f9", "#94a3b8", "#e2e8f0", "○"
    return (
        f'<span style="display:inline-flex;align-items:center;gap:5px;'
        f'padding:4px 13px;border-radius:999px;'
        f'background:{bg};border:1px solid {border};'
        f'color:{color};font-weight:600;font-size:.8rem;white-space:nowrap">'
        f'{icon}&thinsp;{label}</span>'
    )


def _render_step_progress() -> None:
    has_data      = "raw_df"      in st.session_state
    has_processed = "processed_X" in st.session_state
    has_results   = "clusters"    in st.session_state

    badges = "  &nbsp;  ".join([
        _step_badge("Upload",     done=has_data,      active=not has_data),
        _step_badge("EDA",        done=has_data,      active=False),
        _step_badge("Preprocess", done=has_processed, active=has_data and not has_processed),
        _step_badge("Detect",     done=has_results,   active=has_processed and not has_results),
        _step_badge("Results",    done=has_results,   active=False),
        _step_badge("Export",     done=False,         active=has_results),
    ])
    st.markdown(
        f'<div style="padding:6px 0 10px">{badges}</div>',
        unsafe_allow_html=True,
    )


# ── sidebar ────────────────────────────────────────────────────────────────────

_KM_DESC = """
<div style="background:#eff6ff;border-left:3px solid #3b82f6;border-radius:0 8px 8px 0;
            padding:11px 14px;margin:8px 0 14px;font-size:.81rem;color:#1e3a5f;line-height:1.5">
  <strong>K-Means</strong> partitions records into <em>k</em> clusters by minimising
  intra-cluster variance. The cluster with the highest attack ratio is flagged as the
  anomaly cluster.
</div>
"""

_DB_DESC = """
<div style="background:#f0fdf4;border-left:3px solid #22c55e;border-radius:0 8px 8px 0;
            padding:11px 14px;margin:8px 0 14px;font-size:.81rem;color:#14532d;line-height:1.5">
  <strong>DBSCAN</strong> groups dense regions of points. Sparse points are labelled
  <em>noise (−1)</em> and treated as anomalies — no need to pre-specify the number
  of clusters.
</div>
"""


def render_sidebar() -> tuple[str, dict]:
    with st.sidebar:
        st.title("⚙ Settings")
        algorithm = st.selectbox("Algorithm", ["K-Means", "DBSCAN"], key="algorithm")

        if algorithm == "K-Means":
            st.markdown(_KM_DESC, unsafe_allow_html=True)
            n_clusters     = st.slider("Clusters (k)", 2, 20, 5, key="km_k")
            use_pretrained = st.checkbox("Use pre-trained model", value=False, key="km_pretrained")
            params = {"n_clusters": n_clusters, "use_pretrained": use_pretrained}
        else:
            st.markdown(_DB_DESC, unsafe_allow_html=True)
            eps         = st.slider("eps",         0.1, 10.0, 2.0, step=0.1, key="dbscan_eps")
            min_samples = st.slider("min_samples", 2,   50,   10,             key="dbscan_min")
            params = {"eps": eps, "min_samples": min_samples}

        # Live results summary
        if "clusters" in st.session_state:
            st.divider()
            n_an  = int(st.session_state["anomaly_mask"].sum())
            n_tot = len(st.session_state["clusters"])
            rate  = n_an / n_tot * 100
            sil   = st.session_state["metrics"].get("silhouette_score")
            alg_u = st.session_state.get("algorithm_used", algorithm)
            sil_s = f"{sil:.3f}" if sil is not None else "N/A"
            st.markdown(f"""
<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;
            padding:13px 15px;font-size:.82rem;line-height:1.8;color:#374151">
  <div style="font-weight:700;color:#0f172a;margin-bottom:6px">Current Analysis</div>
  <div>📊 &nbsp;<strong>{alg_u}</strong></div>
  <div>🚨 &nbsp;{n_an:,} anomalies &nbsp;({rate:.1f}%)</div>
  <div>📈 &nbsp;Silhouette: <strong>{sil_s}</strong></div>
</div>
""", unsafe_allow_html=True)

        st.divider()
        st.caption("Network Traffic Anomaly Detection")
        st.caption("SUPMTI · AI Capstone 2025-2026")

    return algorithm, params


# ── step 1: upload ─────────────────────────────────────────────────────────────

def render_upload_section() -> None:
    st.header("1 · Upload Dataset")

    uploaded = st.file_uploader(
        "Choose a file — CSV, Excel, or NSL-KDD .txt",
        type=["csv", "xlsx", "xls", "txt"],
        on_change=_clear_downstream,
        key="uploader",
    )

    if uploaded is None:
        _render_empty_state()
        return

    with st.spinner("Loading…"):
        try:
            df = load_from_upload(uploaded)
        except ValueError as exc:
            st.error(str(exc))
            return

    valid, msg = validate_dataframe(df)
    if not valid:
        st.error(f"Validation failed: {msg}")
        return

    st.success(msg)
    summary = get_dataset_summary(df)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows",        f"{summary['n_rows']:,}")
    c2.metric("Columns",     summary["n_cols"])
    c3.metric("Null values", summary["null_count"])
    c4.metric("Duplicates",  summary["duplicate_count"])

    with st.expander("Preview — first 5 rows"):
        st.dataframe(df.head(), use_container_width=True)

    st.session_state["raw_df"]   = df
    st.session_state["filename"] = uploaded.name


# ── step 2: EDA ────────────────────────────────────────────────────────────────

def render_eda_section(df: pd.DataFrame) -> None:
    st.header("2 · Exploratory Data Analysis")
    with st.expander("Show EDA", expanded=False):
        tab1, tab2, tab3, tab4 = st.tabs(["Labels", "Categoricals", "Numerics", "Correlation"])

        with tab1:
            if "label" in df.columns:
                col1, col2 = st.columns(2)
                with col1:
                    st.plotly_chart(_fig_label_dist(df), use_container_width=True)
                with col2:
                    st.plotly_chart(_fig_binary_pie(df), use_container_width=True)
                st.plotly_chart(_fig_attacks(df), use_container_width=True)
            else:
                st.info("No 'label' column — label analysis not available.")

        with tab2:
            st.plotly_chart(_fig_cat_dists(df), use_container_width=True)

        with tab3:
            st.plotly_chart(_fig_num_dists(df), use_container_width=True)

        with tab4:
            st.plotly_chart(_fig_corr(df), use_container_width=True)


# ── step 3: preprocess ─────────────────────────────────────────────────────────

def render_preprocessing_section() -> None:
    st.header("3 · Preprocess Data")
    use_pretrained = st.checkbox(
        "Use pre-trained preprocessor (faster demo)", key="use_pretrained_pre"
    )

    if st.button("Run Preprocessing", key="btn_preprocess", type="primary"):
        df = st.session_state["raw_df"]
        with st.spinner("Preprocessing…"):
            if use_pretrained:
                try:
                    import joblib
                    preprocessor = joblib.load(PROJECT_ROOT / "models" / "preprocessor.pkl")
                    X            = transform_with_existing(df, preprocessor)
                    labels       = df["label"].copy() if "label" in df.columns else None
                except Exception as exc:
                    st.error(f"Could not load pre-trained preprocessor: {exc}")
                    return
            else:
                X, preprocessor, labels = fit_and_transform(df)
                save_processed(X, labels, preprocessor, split="upload")

        st.session_state.update({"processed_X": X, "preprocessor": preprocessor, "labels": labels})
        for k in ["clusters", "anomaly_mask", "metrics", "anomaly_cluster_id", "anomaly_purity"]:
            st.session_state.pop(k, None)

        st.success(f"Done — feature matrix: {X.shape[0]:,} rows × {X.shape[1]} features")


# ── step 4: detection ──────────────────────────────────────────────────────────

def render_detection_section(algorithm: str, params: dict) -> None:
    st.header("4 · Run Detection")

    if st.button("Run Detection", key="btn_detect", type="primary"):
        X      = st.session_state["processed_X"]
        labels = st.session_state.get("labels")

        with st.spinner(f"Running {algorithm}…"):
            if algorithm == "K-Means":
                if params.get("use_pretrained"):
                    try:
                        model    = load_pretrained_kmeans()
                        clusters = predict_kmeans(model, X)
                    except Exception as exc:
                        st.error(f"Could not load pre-trained model: {exc}")
                        return
                else:
                    model    = train_kmeans(X, n_clusters=params["n_clusters"])
                    clusters = predict_kmeans(model, X)

                anomaly_id = 0
                purity     = None
                if labels is not None:
                    try:
                        binary_table, _ = cluster_label_table(clusters, labels)
                        anomaly_id      = identify_anomaly_cluster(binary_table)
                        row             = binary_table.loc[anomaly_id]
                        n_attack        = int(row.get("attack", 0))
                        purity          = round(n_attack / row.sum() * 100, 1)
                    except Exception as exc:
                        st.warning(
                            f"Could not auto-identify anomaly cluster ({exc}). "
                            "Defaulting to cluster 0."
                        )

                anomaly_mask = get_anomaly_mask(clusters, anomaly_id)
                st.session_state["anomaly_cluster_id"] = anomaly_id
                st.session_state["anomaly_purity"]     = purity

            else:
                model        = train_dbscan(X, eps=params["eps"], min_samples=params["min_samples"])
                clusters     = get_dbscan_clusters(model)
                anomaly_mask = get_anomaly_mask_dbscan(clusters)
                summary      = get_dbscan_summary(clusters)
                st.session_state.pop("anomaly_cluster_id", None)
                st.session_state["anomaly_purity"] = None
                if summary["noise_ratio"] > 0.8:
                    st.warning(
                        f"{summary['noise_ratio'] * 100:.1f}% of points flagged as noise — "
                        "try increasing eps or decreasing min_samples."
                    )

        metrics = evaluate_clustering(X, clusters, labels)
        st.session_state.update({
            "clusters":       clusters,
            "anomaly_mask":   anomaly_mask,
            "metrics":        metrics,
            "params":         params,
            "algorithm_used": algorithm,
        })
        st.success("Detection complete.")


# ── step 5: results ────────────────────────────────────────────────────────────

def render_results_section() -> None:
    st.header("5 · Results")

    clusters:     np.ndarray       = st.session_state["clusters"]
    anomaly_mask: np.ndarray       = st.session_state["anomaly_mask"]
    metrics:      dict             = st.session_state["metrics"]
    X:            np.ndarray       = st.session_state["processed_X"]
    labels:       pd.Series | None = st.session_state.get("labels")
    algorithm:    str              = st.session_state.get("algorithm_used", "")
    purity:       float | None     = st.session_state.get("anomaly_purity")

    n_total     = len(clusters)
    n_anomalies = int(anomaly_mask.sum())
    rate        = n_anomalies / n_total * 100

    # ── summary cards ──────────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    c1.metric("Total records",    f"{n_total:,}")
    c2.metric(
        "Anomalies detected", f"{n_anomalies:,}",
        delta=f"{rate:.2f}% of traffic",
        delta_color="inverse",
    )
    c3.metric("Anomaly rate", f"{rate:.2f}%")

    # ── interpretation banner ──────────────────────────────────────────────────
    if algorithm == "K-Means" and "anomaly_cluster_id" in st.session_state:
        cid        = st.session_state["anomaly_cluster_id"]
        purity_str = f", {purity:.1f}% attack purity" if purity is not None else ""
        st.info(
            f"**Cluster {cid}** is the anomaly cluster{purity_str}. "
            f"All {n_anomalies:,} records it contains are flagged as anomalies."
        )
    elif algorithm == "DBSCAN":
        st.info(
            f"DBSCAN labels noise points (cluster = −1) as anomalies. "
            f"{n_anomalies:,} records ({rate:.1f}% of traffic) flagged."
        )

    tab_cluster, tab_error, tab_cross = st.tabs(
        ["Cluster View", "Error Analysis", "Cross-Tables"]
    )

    # ── cluster view ───────────────────────────────────────────────────────────
    with tab_cluster:
        sil = metrics.get("silhouette_score")
        db  = metrics.get("davies_bouldin_score")
        ari = metrics.get("adjusted_rand_index")

        m1, m2, m3 = st.columns(3)
        m1.metric("Silhouette Score",     f"{sil:.4f}" if sil is not None else "N/A")
        m2.metric("Davies-Bouldin Index", f"{db:.4f}"  if db  is not None else "N/A")
        m3.metric("Adj. Rand Index",      f"{ari:.4f}" if ari is not None else "N/A")

        anomaly_cluster_id = st.session_state.get("anomaly_cluster_id", -99)
        counts = (
            pd.Series(clusters)
            .value_counts()
            .sort_index()
            .reset_index()
        )
        counts.columns = ["Cluster", "Count"]
        counts["Type"] = counts["Cluster"].apply(
            lambda c: "Anomaly"
            if (algorithm == "DBSCAN" and c == -1)
            or (algorithm != "DBSCAN" and c == anomaly_cluster_id)
            else "Normal"
        )
        fig_bar = px.bar(
            counts, x="Cluster", y="Count", color="Type",
            color_discrete_map={"Anomaly": _C_ANOMALY, "Normal": _C_NORMAL},
            title="Records per Cluster",
        )
        fig_bar.update_layout(**_CHART, bargap=0.3, showlegend=True)
        fig_bar.update_traces(marker_line_width=0)
        st.plotly_chart(fig_bar, use_container_width=True)

        st.subheader("Cluster Visualization — PCA 2D")
        n_sample = min(5000, X.shape[0])
        idx      = np.random.default_rng(42).choice(X.shape[0], n_sample, replace=False)
        with st.spinner("Computing PCA…"):
            coords = _pca_2d(X[idx])

        scatter_df = pd.DataFrame({
            "PC1":     coords[:, 0],
            "PC2":     coords[:, 1] if coords.shape[1] > 1 else coords[:, 0],
            "Cluster": clusters[idx].astype(str),
            "Type":    np.where(anomaly_mask[idx], "Anomaly", "Normal"),
        })
        fig_scatter = px.scatter(
            scatter_df, x="PC1", y="PC2",
            color="Type", symbol="Cluster",
            color_discrete_map={"Anomaly": _C_ANOMALY, "Normal": _C_NORMAL},
            title=f"PCA 2D Projection — {algorithm} (sample of {n_sample:,})",
            opacity=0.55,
        )
        fig_scatter.update_traces(marker_size=5)
        fig_scatter.update_layout(**_CHART)
        st.plotly_chart(fig_scatter, use_container_width=True)

    # ── error analysis ─────────────────────────────────────────────────────────
    with tab_error:
        if labels is not None:
            err = error_analysis(clusters, labels, anomaly_mask)

            e1, e2, e3, e4 = st.columns(4)
            e1.metric("Precision",       f"{err['precision']:.4f}")
            e2.metric("Recall",          f"{err['recall']:.4f}")
            e3.metric("F1 Score",        f"{err['f1_score']:.4f}")
            e4.metric("False Negatives", f"{err['false_negatives']:,}")

            st.subheader("Missed Attack Types (False Negatives)")
            if not err["missed_attack_types"].empty:
                fn_df = (
                    err["missed_attack_types"]
                    .reset_index()
                )
                fn_df.columns = ["Attack Type", "Count"]
                fig_fn = px.bar(
                    fn_df, x="Count", y="Attack Type", orientation="h",
                    title="Attacks Not Detected",
                    color="Count",
                    color_continuous_scale=["#fca5a5", "#ef4444", "#991b1b"],
                )
                fig_fn.update_layout(
                    **_CHART,
                    yaxis={"categoryorder": "total ascending"},
                    coloraxis_showscale=False,
                )
                fig_fn.update_traces(marker_line_width=0)
                st.plotly_chart(fig_fn, use_container_width=True)
            else:
                st.success("All attack types were detected.")

            st.subheader("Attack Types per Cluster")
            st.dataframe(
                err["attack_type_per_cluster"].style.background_gradient(
                    subset=["count"], cmap="Blues"
                ),
                use_container_width=True,
            )
        else:
            st.info("Error analysis requires a dataset with a 'label' column (NSL-KDD format).")

    # ── cross-tables ───────────────────────────────────────────────────────────
    with tab_cross:
        if labels is not None:
            binary_table, original_table = cluster_label_table(clusters, labels)
            t1, t2 = st.tabs(["Binary (normal / attack)", "Original labels"])
            with t1:
                st.dataframe(
                    binary_table.style.background_gradient(cmap="RdYlGn_r"),
                    use_container_width=True,
                )
            with t2:
                st.dataframe(original_table, use_container_width=True)
        else:
            st.info("Cross-tables require a 'label' column.")


# ── step 6: export ─────────────────────────────────────────────────────────────

def render_export_section() -> None:
    st.header("6 · Export & Save")

    clusters     = st.session_state["clusters"]
    anomaly_mask = st.session_state["anomaly_mask"]
    raw_df       = st.session_state["raw_df"]
    metrics      = st.session_state["metrics"]
    params       = st.session_state.get("params", {})
    algorithm    = st.session_state.get("algorithm_used", "unknown")
    filename     = st.session_state.get("filename", "upload")

    export_df               = raw_df.copy().iloc[: len(clusters)]
    export_df["cluster"]    = clusters
    export_df["is_anomaly"] = anomaly_mask

    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button(
            "⬇ Download CSV",
            data=export_df.to_csv(index=False).encode(),
            file_name=f"anomaly_report_{algorithm.lower()}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with c2:
        pdf_bytes = _build_pdf(
            filename, algorithm,
            len(clusters), int(anomaly_mask.sum()),
            float(anomaly_mask.sum() / len(clusters)),
            metrics.get("silhouette_score"),
            metrics.get("davies_bouldin_score"),
            metrics.get("adjusted_rand_index"),
            json.dumps(params, sort_keys=True),
        )
        st.download_button(
            "⬇ Download PDF",
            data=pdf_bytes,
            file_name=f"anomaly_report_{algorithm.lower()}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    with c3:
        if st.button("💾 Save to History", key="btn_save_history", use_container_width=True):
            save_analysis(filename, algorithm, len(clusters),
                          int(anomaly_mask.sum()), metrics, params)
            st.success("Saved.")


@st.cache_data(show_spinner=False)
def _build_pdf(
    filename: str,
    algorithm: str,
    n_records: int,
    n_anomalies: int,
    anomaly_ratio: float,
    silhouette,
    db_index,
    ari,
    params_json: str,
) -> bytes:
    try:
        from fpdf import FPDF
    except ImportError:
        return b"fpdf2 not installed."

    params = json.loads(params_json)
    pdf    = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Network Traffic Anomaly Detection Report", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "SUPMTI Rabat | AI Capstone 2025-2026 | Project 15", ln=True)
    pdf.ln(4)

    rows = [
        ("File",                 filename),
        ("Algorithm",            algorithm),
        ("Total records",        f"{n_records:,}"),
        ("Anomalies detected",   f"{n_anomalies:,}"),
        ("Anomaly rate",         f"{anomaly_ratio * 100:.2f}%"),
        ("Silhouette Score",     f"{silhouette:.4f}" if silhouette is not None else "N/A"),
        ("Davies-Bouldin Index", f"{db_index:.4f}"   if db_index   is not None else "N/A"),
        ("Adjusted Rand Index",  f"{ari:.4f}"        if ari        is not None else "N/A"),
    ]
    for label, value in rows:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(75, 8, label + ":", border=0)
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 8, str(value), ln=True)

    if params:
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "Parameters:", ln=True)
        pdf.set_font("Helvetica", "", 11)
        for k, v in params.items():
            pdf.cell(0, 8, f"  {k}: {v}", ln=True)

    return pdf.output()


# ── history ────────────────────────────────────────────────────────────────────

def render_history_section() -> None:
    df = get_history()
    if df.empty:
        st.info("No analyses saved yet. Run a detection and click 'Save to History'.")
        return

    display = df.drop(columns=["params_json"], errors="ignore").rename(columns={
        "id":                   "ID",
        "timestamp":            "Time",
        "filename":             "File",
        "algorithm":            "Algorithm",
        "n_records":            "Records",
        "n_anomalies":          "Anomalies",
        "anomaly_ratio":        "Ratio",
        "silhouette_score":     "Silhouette",
        "davies_bouldin_score": "DB Index",
        "adjusted_rand_index":  "ARI",
    })
    st.dataframe(display, use_container_width=True)

    with st.expander("Delete an entry"):
        row_id = st.number_input("Row ID", min_value=1, step=1, key="del_id")
        if st.button("Delete", key="btn_del"):
            delete_analysis(int(row_id))
            st.success(f"Row {row_id} deleted.")
            st.rerun()


# ── main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    st.set_page_config(
        page_title="Network Anomaly Detector",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _inject_css()
    init_db()

    algorithm, params = render_sidebar()

    st.title("Network Traffic Anomaly Detection")
    st.caption("Project 15 — Unsupervised Clustering · SUPMTI AI Capstone 2025-2026 · Pr. Soufiane HAMIDA")
    _render_step_progress()
    st.divider()

    render_upload_section()

    if "raw_df" in st.session_state:
        st.divider()
        render_eda_section(st.session_state["raw_df"])
        st.divider()
        render_preprocessing_section()

    if "processed_X" in st.session_state:
        st.divider()
        render_detection_section(algorithm, params)

    if "clusters" in st.session_state:
        st.divider()
        render_results_section()
        st.divider()
        render_export_section()

    st.divider()
    with st.expander("Analysis History"):
        render_history_section()


if __name__ == "__main__":
    main()
