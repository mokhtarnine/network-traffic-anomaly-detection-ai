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
from src.data.preprocessor import fit_and_transform, transform_with_existing, save_processed
from src.eda.eda_analysis import (
    basic_summary, fig_label_distribution, fig_binary_pie,
    fig_categorical_distributions, fig_numeric_distributions,
    fig_correlation_heatmap, fig_attack_types,
)
from src.evaluation.metrics import (
    cluster_label_table, evaluate_clustering,
    identify_anomaly_cluster, error_analysis,
)
from src.models.dbscan_model import (
    get_anomaly_mask_dbscan, get_dbscan_clusters,
    get_dbscan_summary, train_dbscan,
)
from src.models.kmeans_model import (
    get_anomaly_mask, load_pretrained_kmeans,
    predict_kmeans, train_kmeans,
)

# ── helpers ───────────────────────────────────────────────────────────────────

STATE_DOWNSTREAM = ["processed_X", "labels", "preprocessor", "clusters", "anomaly_mask", "metrics"]


def _clear_downstream():
    for key in STATE_DOWNSTREAM:
        st.session_state.pop(key, None)


def _pca_2d(X: np.ndarray) -> np.ndarray:
    n = min(2, X.shape[1])
    return PCA(n_components=n, random_state=42).fit_transform(X)


# ── sidebar ───────────────────────────────────────────────────────────────────

def render_sidebar() -> tuple[str, dict]:
    with st.sidebar:
        st.title("Settings")
        algorithm = st.selectbox("Algorithm", ["K-Means", "DBSCAN"], key="algorithm")

        st.subheader("Parameters")
        if algorithm == "K-Means":
            n_clusters = st.slider("Clusters (k)", 2, 20, 5, key="km_k")
            use_pretrained = st.checkbox("Use pre-trained model", value=False, key="km_pretrained")
            params = {"n_clusters": n_clusters, "use_pretrained": use_pretrained}
        else:
            eps = st.slider("eps", 0.1, 10.0, 2.0, step=0.1, key="dbscan_eps")
            min_samples = st.slider("min_samples", 2, 50, 10, key="dbscan_min")
            params = {"eps": eps, "min_samples": min_samples}

        st.divider()
        st.caption("Network Traffic Anomaly Detection")
        st.caption("SUPMTI · AI Capstone 2025-2026")
    return algorithm, params


# ── step 1: upload ────────────────────────────────────────────────────────────

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
    c1.metric("Rows", f"{summary['n_rows']:,}")
    c2.metric("Columns", summary["n_cols"])
    c3.metric("Null values", summary["null_count"])
    c4.metric("Duplicates", summary["duplicate_count"])

    with st.expander("Preview (first 5 rows)"):
        st.dataframe(df.head())

    st.session_state["raw_df"] = df
    st.session_state["filename"] = uploaded.name


# ── step 2: EDA ───────────────────────────────────────────────────────────────

def render_eda_section(df: pd.DataFrame):
    st.header("2 · Exploratory Data Analysis")
    with st.expander("Show EDA", expanded=False):
        tab1, tab2, tab3, tab4 = st.tabs(["Labels", "Categoricals", "Numerics", "Correlation"])

        with tab1:
            if "label" in df.columns:
                c1, c2 = st.columns(2)
                with c1:
                    st.plotly_chart(fig_label_distribution(df), use_container_width=True)
                with c2:
                    st.plotly_chart(fig_binary_pie(df), use_container_width=True)
                if "label" in df.columns:
                    st.plotly_chart(fig_attack_types(df), use_container_width=True)
            else:
                st.info("No 'label' column — label analysis not available.")

        with tab2:
            st.plotly_chart(fig_categorical_distributions(df), use_container_width=True)

        with tab3:
            st.plotly_chart(fig_numeric_distributions(df), use_container_width=True)

        with tab4:
            st.plotly_chart(fig_correlation_heatmap(df), use_container_width=True)


# ── step 3: preprocess ────────────────────────────────────────────────────────

def render_preprocessing_section():
    st.header("3 · Preprocess Data")
    use_pretrained = st.checkbox("Use pre-trained preprocessor (faster demo)", key="use_pretrained_pre")

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
                save_processed(X, labels, preprocessor, split="upload")

        st.session_state.update({
            "processed_X": X, "preprocessor": preprocessor,
            "labels": labels,
        })
        for k in ["clusters", "anomaly_mask", "metrics"]:
            st.session_state.pop(k, None)

        st.success(f"Done — feature matrix: {X.shape[0]:,} rows × {X.shape[1]} features")


# ── step 4: detection ─────────────────────────────────────────────────────────

def render_detection_section(algorithm: str, params: dict):
    st.header("4 · Run Detection")

    if st.button("Run Detection", key="btn_detect"):
        X = st.session_state["processed_X"]
        labels = st.session_state.get("labels")

        with st.spinner(f"Running {algorithm}…"):
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
                st.session_state["anomaly_cluster_id"] = anomaly_id

            else:
                model = train_dbscan(X, eps=params["eps"], min_samples=params["min_samples"])
                clusters = get_dbscan_clusters(model)
                anomaly_mask = get_anomaly_mask_dbscan(clusters)
                summary = get_dbscan_summary(clusters)
                if summary["noise_ratio"] > 0.8:
                    st.warning(
                        f"{summary['noise_ratio']*100:.1f}% flagged as noise — "
                        "try increasing eps or decreasing min_samples."
                    )

        metrics = evaluate_clustering(X, clusters, labels)
        st.session_state.update({
            "clusters": clusters, "anomaly_mask": anomaly_mask,
            "metrics": metrics, "params": params,
            "algorithm_used": algorithm,
        })
        st.success("Detection complete.")


# ── step 5: results ───────────────────────────────────────────────────────────

def render_results_section():
    st.header("5 · Results")

    clusters: np.ndarray = st.session_state["clusters"]
    anomaly_mask: np.ndarray = st.session_state["anomaly_mask"]
    metrics: dict = st.session_state["metrics"]
    X: np.ndarray = st.session_state["processed_X"]
    labels: pd.Series | None = st.session_state.get("labels")
    algorithm = st.session_state.get("algorithm_used", "")

    n_total = len(clusters)
    n_anomalies = int(anomaly_mask.sum())

    # ── metric cards ──
    c1, c2, c3 = st.columns(3)
    c1.metric("Total records", f"{n_total:,}")
    c2.metric("Anomalies detected", f"{n_anomalies:,}")
    c3.metric("Anomaly rate", f"{n_anomalies/n_total*100:.2f}%")

    tab_cluster, tab_error, tab_cross = st.tabs(["Cluster View", "Error Analysis", "Cross-Tables"])

    # ── cluster view ──
    with tab_cluster:
        m1, m2, m3 = st.columns(3)
        sil = metrics.get("silhouette_score")
        db  = metrics.get("davies_bouldin_score")
        ari = metrics.get("adjusted_rand_index")
        m1.metric("Silhouette Score",    f"{sil:.4f}" if sil is not None else "N/A")
        m2.metric("Davies-Bouldin Index",f"{db:.4f}"  if db  is not None else "N/A")
        m3.metric("Adj. Rand Index",     f"{ari:.4f}" if ari is not None else "N/A (no labels)")

        # Cluster bar chart
        counts = pd.Series(clusters).value_counts().sort_index().reset_index()
        counts.columns = ["Cluster", "Count"]
        counts["Type"] = counts["Cluster"].apply(
            lambda c: "Anomaly" if (
                (algorithm == "DBSCAN" and c == -1) or
                (algorithm != "DBSCAN" and c == st.session_state.get("anomaly_cluster_id", -99))
            ) else "Normal"
        )
        fig_bar = px.bar(
            counts, x="Cluster", y="Count", color="Type",
            color_discrete_map={"Anomaly": "#EF553B", "Normal": "#636EFA"},
            title="Records per Cluster",
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        # PCA scatter
        st.subheader("Cluster Visualization (PCA 2D)")
        with st.spinner("Computing PCA…"):
            n_sample = min(5000, X.shape[0])
            idx = np.random.default_rng(42).choice(X.shape[0], n_sample, replace=False)
            coords = _pca_2d(X[idx])

        scatter_df = pd.DataFrame({
            "PC1": coords[:, 0],
            "PC2": coords[:, 1] if coords.shape[1] > 1 else coords[:, 0],
            "Cluster": clusters[idx].astype(str),
            "Anomaly": np.where(anomaly_mask[idx], "Anomaly", "Normal"),
        })
        fig_scatter = px.scatter(
            scatter_df, x="PC1", y="PC2", color="Anomaly", symbol="Cluster",
            color_discrete_map={"Anomaly": "#EF553B", "Normal": "#636EFA"},
            title=f"PCA 2D — {algorithm} (sample of {n_sample:,})", opacity=0.6,
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    # ── error analysis ──
    with tab_error:
        if labels is not None:
            err = error_analysis(clusters, labels, anomaly_mask)
            e1, e2, e3, e4 = st.columns(4)
            e1.metric("Precision", f"{err['precision']:.4f}")
            e2.metric("Recall",    f"{err['recall']:.4f}")
            e3.metric("F1 Score",  f"{err['f1_score']:.4f}")
            e4.metric("False Negatives", f"{err['false_negatives']:,}")

            st.subheader("Missed Attack Types (False Negatives)")
            if not err["missed_attack_types"].empty:
                fn_df = err["missed_attack_types"].reset_index()
                fn_df.columns = ["Attack Type", "Count"]
                fig_fn = px.bar(
                    fn_df, x="Count", y="Attack Type", orientation="h",
                    title="Attacks Not Detected", color="Count",
                    color_continuous_scale="Reds",
                )
                fig_fn.update_layout(yaxis={"categoryorder": "total ascending"},
                                     coloraxis_showscale=False)
                st.plotly_chart(fig_fn, use_container_width=True)
            else:
                st.success("All attack types were detected.")

            st.subheader("Attack Types per Cluster")
            st.dataframe(err["attack_type_per_cluster"], use_container_width=True)
        else:
            st.info("Error analysis requires a dataset with a 'label' column (NSL-KDD format).")

    # ── cross-tables ──
    with tab_cross:
        if labels is not None:
            binary_table, original_table = cluster_label_table(clusters, labels)
            t1, t2 = st.tabs(["Binary (normal / attack)", "Original labels"])
            with t1:
                st.dataframe(binary_table, use_container_width=True)
            with t2:
                st.dataframe(original_table, use_container_width=True)
        else:
            st.info("Cross-tables require a 'label' column.")


# ── step 6: export ────────────────────────────────────────────────────────────

def render_export_section():
    st.header("6 · Export & Save")

    clusters     = st.session_state["clusters"]
    anomaly_mask = st.session_state["anomaly_mask"]
    raw_df       = st.session_state["raw_df"]
    metrics      = st.session_state["metrics"]
    params       = st.session_state.get("params", {})
    algorithm    = st.session_state.get("algorithm_used", "unknown")
    filename     = st.session_state.get("filename", "upload")

    export_df = raw_df.copy().iloc[: len(clusters)]
    export_df["cluster"]    = clusters
    export_df["is_anomaly"] = anomaly_mask

    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button(
            "Download CSV report",
            data=export_df.to_csv(index=False).encode(),
            file_name=f"anomaly_report_{algorithm.lower()}.csv",
            mime="text/csv",
        )
    with c2:
        pdf_bytes = _build_pdf(filename, algorithm, clusters, anomaly_mask, metrics, params)
        st.download_button(
            "Download PDF report",
            data=pdf_bytes,
            file_name=f"anomaly_report_{algorithm.lower()}.pdf",
            mime="application/pdf",
        )
    with c3:
        if st.button("Save to History"):
            save_analysis(filename, algorithm, len(clusters),
                          int(anomaly_mask.sum()), metrics, params)
            st.success("Saved to analysis history.")


def _build_pdf(filename, algorithm, clusters, anomaly_mask, metrics, params) -> bytes:
    try:
        from fpdf import FPDF
    except ImportError:
        return b"fpdf2 not installed."

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Network Traffic Anomaly Detection Report", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "SUPMTI Rabat | AI Capstone 2025-2026 | Project 15", ln=True)
    pdf.ln(4)

    rows = [
        ("File", filename),
        ("Algorithm", algorithm),
        ("Total records", f"{len(clusters):,}"),
        ("Anomalies detected", f"{int(anomaly_mask.sum()):,}"),
        ("Anomaly rate", f"{anomaly_mask.sum()/len(clusters)*100:.2f}%"),
        ("Silhouette Score", str(metrics.get("silhouette_score", "N/A"))),
        ("Davies-Bouldin Index", str(metrics.get("davies_bouldin_score", "N/A"))),
        ("Adjusted Rand Index", str(metrics.get("adjusted_rand_index", "N/A"))),
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


# ── history ───────────────────────────────────────────────────────────────────

def render_history_section():
    df = get_history()
    if df.empty:
        st.info("No analyses saved yet.")
        return
    st.dataframe(df.drop(columns=["params_json"], errors="ignore"), use_container_width=True)
    with st.expander("Delete an entry"):
        row_id = st.number_input("Row ID", min_value=1, step=1, key="del_id")
        if st.button("Delete", key="btn_del"):
            delete_analysis(int(row_id))
            st.success(f"Row {row_id} deleted.")
            st.rerun()


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title="Network Anomaly Detector",
        page_icon="🔍",
        layout="wide",
    )
    init_db()

    algorithm, params = render_sidebar()

    st.title("Network Traffic Anomaly Detection")
    st.caption("Project 15 — Clustering | SUPMTI AI Capstone 2025-2026")

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
