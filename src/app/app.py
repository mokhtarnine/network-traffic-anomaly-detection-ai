import io
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
from src.data.preprocessor import fit_and_transform, transform_with_existing
from src.evaluation.metrics import (
    cluster_label_table,
    evaluate_clustering,
    identify_anomaly_cluster,
)
from src.models.dbscan_model import (
    get_anomaly_mask_dbscan,
    get_dbscan_clusters,
    get_dbscan_summary,
    train_dbscan,
)
from src.models.kmeans_model import (
    get_anomaly_mask,
    load_pretrained_kmeans,
    predict_kmeans,
    train_kmeans,
)

# ── helpers ──────────────────────────────────────────────────────────────────

STATE_DOWNSTREAM = ["processed_X", "labels", "preprocessor", "clusters", "anomaly_mask", "metrics"]


def _clear_downstream():
    for key in STATE_DOWNSTREAM:
        st.session_state.pop(key, None)


def _pca_2d(X: np.ndarray) -> np.ndarray:
    n_components = min(2, X.shape[1])
    return PCA(n_components=n_components, random_state=42).fit_transform(X)


# ── sections ─────────────────────────────────────────────────────────────────

def render_upload_section():
    st.header("1 · Upload Dataset")
    uploaded = st.file_uploader(
        "Choose a file (CSV, Excel, or NSL-KDD .txt)",
        type=["csv", "xlsx", "xls", "txt"],
        on_change=_clear_downstream,
        key="uploader",
    )

    if uploaded is None:
        st.info("Upload a network traffic dataset to begin.")
        return

    with st.spinner("Loading file…"):
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

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Rows", f"{summary['n_rows']:,}")
    col2.metric("Columns", summary["n_cols"])
    col3.metric("Null values", summary["null_count"])
    col4.metric("Duplicates", summary["duplicate_count"])

    with st.expander("Preview (first 5 rows)"):
        st.dataframe(df.head())

    st.session_state["raw_df"] = df
    st.session_state["filename"] = uploaded.name


def render_preprocessing_section():
    st.header("2 · Preprocess Data")

    use_pretrained = st.checkbox(
        "Use pre-trained preprocessor (faster demo)",
        value=False,
        key="use_pretrained_pre",
    )

    if st.button("Run Preprocessing", key="btn_preprocess"):
        df = st.session_state["raw_df"]
        with st.spinner("Preprocessing…"):
            if use_pretrained:
                try:
                    import joblib
                    preprocessor = joblib.load(PROJECT_ROOT / "models" / "preprocessor.pkl")
                    X = transform_with_existing(df, preprocessor)
                    labels = df["label"].copy() if "label" in df.columns else None
                except Exception as exc:
                    st.error(f"Could not load pre-trained preprocessor: {exc}")
                    return
            else:
                X, preprocessor, labels = fit_and_transform(df)

        st.session_state["processed_X"] = X
        st.session_state["preprocessor"] = preprocessor
        st.session_state["labels"] = labels
        st.session_state.pop("clusters", None)
        st.session_state.pop("anomaly_mask", None)
        st.session_state.pop("metrics", None)

        st.success(f"Preprocessing complete — feature matrix shape: {X.shape}")


def render_detection_section():
    st.header("3 · Run Detection")

    with st.sidebar:
        st.subheader("Algorithm")
        algorithm = st.selectbox("Select algorithm", ["K-Means", "DBSCAN"], key="algorithm")

        if algorithm == "K-Means":
            n_clusters = st.slider("Number of clusters (k)", 2, 20, 5, key="km_k")
            use_pretrained_model = st.checkbox("Use pre-trained K-Means model", value=False, key="use_pretrained_km")
            params = {"n_clusters": n_clusters, "use_pretrained": use_pretrained_model}
        else:
            eps = st.slider("eps", 0.1, 10.0, 2.0, step=0.1, key="dbscan_eps")
            min_samples = st.slider("min_samples", 2, 50, 10, key="dbscan_min")
            params = {"eps": eps, "min_samples": min_samples}

    if st.button("Run Detection", key="btn_detect"):
        X = st.session_state["processed_X"]
        labels = st.session_state.get("labels")

        with st.spinner(f"Running {algorithm}… (may take a moment on large datasets)"):
            if algorithm == "K-Means":
                if params.get("use_pretrained"):
                    try:
                        model = load_pretrained_kmeans()
                        clusters = predict_kmeans(model, X)
                    except Exception as exc:
                        st.error(f"Could not load pre-trained model: {exc}")
                        return
                else:
                    model = train_kmeans(X, n_clusters=params["n_clusters"])
                    clusters = predict_kmeans(model, X)

                if labels is not None:
                    try:
                        binary_table, _ = cluster_label_table(clusters, labels)
                        anomaly_id = identify_anomaly_cluster(binary_table)
                    except Exception:
                        anomaly_id = 0
                else:
                    anomaly_id = 0
                anomaly_mask = get_anomaly_mask(clusters, anomaly_id)

            else:  # DBSCAN
                model = train_dbscan(X, eps=params["eps"], min_samples=params["min_samples"])
                clusters = get_dbscan_clusters(model)
                anomaly_mask = get_anomaly_mask_dbscan(clusters)
                dbscan_info = get_dbscan_summary(clusters)

                if dbscan_info["noise_ratio"] > 0.8:
                    st.warning(
                        f"{dbscan_info['noise_ratio']*100:.1f}% of points flagged as noise. "
                        "Try increasing eps or decreasing min_samples."
                    )

        metrics = evaluate_clustering(X, clusters, labels)

        st.session_state["clusters"] = clusters
        st.session_state["anomaly_mask"] = anomaly_mask
        st.session_state["metrics"] = metrics
        st.session_state["params"] = params
        st.session_state["algorithm_used"] = algorithm
        st.success("Detection complete.")


def render_results_section():
    st.header("4 · Results")

    clusters: np.ndarray = st.session_state["clusters"]
    anomaly_mask: np.ndarray = st.session_state["anomaly_mask"]
    metrics: dict = st.session_state["metrics"]
    X: np.ndarray = st.session_state["processed_X"]
    labels: pd.Series | None = st.session_state.get("labels")
    algorithm = st.session_state.get("algorithm_used", "")

    n_total = len(clusters)
    n_anomalies = int(anomaly_mask.sum())
    anomaly_pct = n_anomalies / n_total * 100

    # ── metric cards ──
    col1, col2, col3 = st.columns(3)
    col1.metric("Total records", f"{n_total:,}")
    col2.metric("Anomalies detected", f"{n_anomalies:,}")
    col3.metric("Anomaly rate", f"{anomaly_pct:.2f}%")

    # ── evaluation scores ──
    st.subheader("Evaluation Metrics")
    m_col1, m_col2, m_col3 = st.columns(3)
    sil = metrics.get("silhouette_score")
    db = metrics.get("davies_bouldin_score")
    ari = metrics.get("adjusted_rand_index")
    m_col1.metric("Silhouette Score", f"{sil:.4f}" if sil is not None else "N/A")
    m_col2.metric("Davies-Bouldin Index", f"{db:.4f}" if db is not None else "N/A")
    m_col3.metric("Adjusted Rand Index", f"{ari:.4f}" if ari is not None else "N/A (no labels)")

    # ── cluster distribution ──
    st.subheader("Cluster Distribution")
    cluster_counts = pd.Series(clusters).value_counts().sort_index().reset_index()
    cluster_counts.columns = ["Cluster", "Count"]
    cluster_counts["Type"] = cluster_counts["Cluster"].apply(
        lambda c: "Anomaly" if (algorithm == "DBSCAN" and c == -1)
        else ("Anomaly" if anomaly_mask[clusters == c].all() else "Normal")
    )
    fig_bar = px.bar(
        cluster_counts,
        x="Cluster",
        y="Count",
        color="Type",
        color_discrete_map={"Anomaly": "#EF553B", "Normal": "#636EFA"},
        title="Records per Cluster",
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # ── 2-D scatter ──
    st.subheader("Cluster Visualization (PCA 2D)")
    with st.spinner("Computing PCA…"):
        sample_size = min(5000, X.shape[0])
        idx = np.random.default_rng(42).choice(X.shape[0], sample_size, replace=False)
        coords = _pca_2d(X[idx])

    scatter_df = pd.DataFrame({"PC1": coords[:, 0], "PC2": coords[:, 1] if coords.shape[1] > 1 else coords[:, 0]})
    scatter_df["Cluster"] = clusters[idx].astype(str)
    scatter_df["Anomaly"] = np.where(anomaly_mask[idx], "Anomaly", "Normal")

    fig_scatter = px.scatter(
        scatter_df,
        x="PC1",
        y="PC2",
        color="Anomaly",
        symbol="Cluster",
        color_discrete_map={"Anomaly": "#EF553B", "Normal": "#636EFA"},
        title=f"PCA 2D — {algorithm} clusters (sample of {sample_size:,} records)",
        opacity=0.6,
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    # ── label cross-table ──
    if labels is not None:
        st.subheader("Cluster vs Label Cross-Table")
        binary_table, original_table = cluster_label_table(clusters, labels)
        tab1, tab2 = st.tabs(["Binary (normal / attack)", "Original labels"])
        with tab1:
            st.dataframe(binary_table)
        with tab2:
            st.dataframe(original_table)


def render_export_section():
    st.header("5 · Export & Save")

    clusters: np.ndarray = st.session_state["clusters"]
    anomaly_mask: np.ndarray = st.session_state["anomaly_mask"]
    raw_df: pd.DataFrame = st.session_state["raw_df"]
    metrics: dict = st.session_state["metrics"]
    params: dict = st.session_state.get("params", {})
    algorithm = st.session_state.get("algorithm_used", "unknown")
    filename = st.session_state.get("filename", "upload")

    export_df = raw_df.copy().iloc[: len(clusters)]
    export_df["cluster"] = clusters
    export_df["is_anomaly"] = anomaly_mask

    col_csv, col_pdf, col_save = st.columns(3)

    # CSV download
    with col_csv:
        csv_bytes = export_df.to_csv(index=False).encode()
        st.download_button(
            label="Download CSV report",
            data=csv_bytes,
            file_name=f"anomaly_report_{algorithm.lower()}.csv",
            mime="text/csv",
        )

    # PDF download
    with col_pdf:
        pdf_bytes = _build_pdf(filename, algorithm, clusters, anomaly_mask, metrics, params)
        st.download_button(
            label="Download PDF report",
            data=pdf_bytes,
            file_name=f"anomaly_report_{algorithm.lower()}.pdf",
            mime="application/pdf",
        )

    # Save to history
    with col_save:
        if st.button("Save to History", key="btn_save"):
            save_analysis(
                filename=filename,
                algorithm=algorithm,
                n_records=len(clusters),
                n_anomalies=int(anomaly_mask.sum()),
                metrics=metrics,
                params=params,
            )
            st.success("Saved to analysis history.")


def _build_pdf(filename, algorithm, clusters, anomaly_mask, metrics, params) -> bytes:
    try:
        from fpdf import FPDF
    except ImportError:
        return b"fpdf2 not installed. Run: pip install fpdf2"

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Network Traffic Anomaly Detection Report", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.ln(4)

    rows = [
        ("File", filename),
        ("Algorithm", algorithm),
        ("Total records", f"{len(clusters):,}"),
        ("Anomalies detected", f"{int(anomaly_mask.sum()):,}"),
        ("Anomaly rate", f"{anomaly_mask.sum() / len(clusters) * 100:.2f}%"),
        ("Silhouette Score", str(metrics.get("silhouette_score", "N/A"))),
        ("Davies-Bouldin Index", str(metrics.get("davies_bouldin_score", "N/A"))),
        ("Adjusted Rand Index", str(metrics.get("adjusted_rand_index", "N/A"))),
    ]
    for label, value in rows:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(70, 8, label + ":", border=0)
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 8, value, ln=True)

    if params:
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "Algorithm Parameters:", ln=True)
        pdf.set_font("Helvetica", "", 11)
        for k, v in params.items():
            pdf.cell(0, 8, f"  {k}: {v}", ln=True)

    return pdf.output()


def render_history_section():
    df = get_history()
    if df.empty:
        st.info("No analyses saved yet.")
        return

    st.dataframe(df.drop(columns=["params_json"], errors="ignore"), use_container_width=True)

    with st.expander("Delete an entry"):
        row_id = st.number_input("Row ID to delete", min_value=1, step=1, key="del_id")
        if st.button("Delete", key="btn_del"):
            delete_analysis(int(row_id))
            st.success(f"Row {row_id} deleted.")
            st.rerun()


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title="Network Anomaly Detector",
        page_icon="🔍",
        layout="wide",
    )
    init_db()

    st.title("Network Traffic Anomaly Detection")
    st.caption("Upload a dataset, select an algorithm, and detect anomalous traffic patterns.")

    render_upload_section()

    if "raw_df" in st.session_state:
        st.divider()
        render_preprocessing_section()

    if "processed_X" in st.session_state:
        st.divider()
        render_detection_section()

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
