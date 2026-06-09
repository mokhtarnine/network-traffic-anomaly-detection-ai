import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


CATEGORICAL_COLUMNS = ["protocol_type", "service", "flag"]
DROP_COLUMNS = ["label", "difficulty", "binary_label"]


# ── summary ──────────────────────────────────────────────────────────────────

def basic_summary(df: pd.DataFrame) -> dict:
    return {
        "shape": df.shape,
        "missing_total": int(df.isna().sum().sum()),
        "missing_per_col": df.isna().sum().to_dict(),
        "duplicates": int(df.duplicated().sum()),
        "dtypes": df.dtypes.astype(str).to_dict(),
    }


def label_distribution(df: pd.DataFrame) -> pd.DataFrame:
    counts = df["label"].value_counts().reset_index()
    counts.columns = ["label", "count"]
    counts["binary"] = counts["label"].apply(
        lambda x: "normal" if str(x).strip().lower() == "normal" else "attack"
    )
    return counts


def binary_distribution(df: pd.DataFrame) -> pd.Series:
    return df["label"].apply(
        lambda x: "normal" if str(x).strip().lower() == "normal" else "attack"
    ).value_counts()


# ── figures ───────────────────────────────────────────────────────────────────

def fig_label_distribution(df: pd.DataFrame) -> go.Figure:
    dist = label_distribution(df)
    top = dist.head(15)
    fig = px.bar(
        top,
        x="label",
        y="count",
        color="binary",
        color_discrete_map={"normal": "#636EFA", "attack": "#EF553B"},
        title="Top 15 Traffic Label Distribution",
        labels={"label": "Label", "count": "Count", "binary": "Type"},
    )
    fig.update_layout(xaxis_tickangle=-35)
    return fig


def fig_binary_pie(df: pd.DataFrame) -> go.Figure:
    binary = binary_distribution(df)
    fig = px.pie(
        values=binary.values,
        names=binary.index,
        title="Normal vs Attack Traffic",
        color=binary.index,
        color_discrete_map={"normal": "#636EFA", "attack": "#EF553B"},
        hole=0.4,
    )
    return fig


def fig_categorical_distributions(df: pd.DataFrame) -> go.Figure:
    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=CATEGORICAL_COLUMNS,
    )
    colors = px.colors.qualitative.Plotly
    for i, col in enumerate(CATEGORICAL_COLUMNS, start=1):
        vc = df[col].value_counts().head(10)
        fig.add_trace(
            go.Bar(x=vc.index.tolist(), y=vc.values.tolist(),
                   name=col, marker_color=colors[i % len(colors)]),
            row=1, col=i,
        )
    fig.update_layout(title="Categorical Feature Distributions (top 10)", showlegend=False)
    return fig


def fig_numeric_distributions(df: pd.DataFrame, n_cols: int = 4) -> go.Figure:
    num_cols = [c for c in df.columns if c not in CATEGORICAL_COLUMNS + DROP_COLUMNS
                and pd.api.types.is_numeric_dtype(df[c])][:12]
    n_rows = int(np.ceil(len(num_cols) / n_cols))
    fig = make_subplots(rows=n_rows, cols=n_cols, subplot_titles=num_cols)
    for idx, col in enumerate(num_cols):
        r, c = divmod(idx, n_cols)
        fig.add_trace(
            go.Histogram(x=df[col], name=col, nbinsx=30, showlegend=False),
            row=r + 1, col=c + 1,
        )
    fig.update_layout(title="Numeric Feature Distributions", height=250 * n_rows)
    return fig


def fig_correlation_heatmap(df: pd.DataFrame, top_n: int = 20) -> go.Figure:
    num_df = df.select_dtypes(include="number").drop(
        columns=[c for c in ["difficulty"] if c in df.columns]
    )
    # pick top_n most-variant columns to keep the heatmap readable
    top_cols = num_df.std().nlargest(top_n).index.tolist()
    corr = num_df[top_cols].corr()
    fig = px.imshow(
        corr,
        color_continuous_scale="RdBu_r",
        zmin=-1, zmax=1,
        title=f"Correlation Heatmap (top {top_n} numeric features by variance)",
        aspect="auto",
    )
    return fig


def fig_attack_types(df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    attacks = df[df["label"].str.strip().str.lower() != "normal"]["label"].value_counts().head(top_n)
    fig = px.bar(
        x=attacks.values,
        y=attacks.index,
        orientation="h",
        title=f"Top {top_n} Attack Types",
        labels={"x": "Count", "y": "Attack Type"},
        color=attacks.values,
        color_continuous_scale="Reds",
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False)
    return fig


def fig_feature_by_binary_label(df: pd.DataFrame, feature: str) -> go.Figure:
    plot_df = df[[feature, "label"]].copy()
    plot_df["binary"] = plot_df["label"].apply(
        lambda x: "normal" if str(x).strip().lower() == "normal" else "attack"
    )
    fig = px.box(
        plot_df, x="binary", y=feature,
        color="binary",
        color_discrete_map={"normal": "#636EFA", "attack": "#EF553B"},
        title=f"{feature} — normal vs attack",
        points=False,
    )
    return fig
