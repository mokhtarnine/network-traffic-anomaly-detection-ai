import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


CATEGORICAL_COLUMNS = ["protocol_type", "service", "flag"]
DROP_COLUMNS        = ["label", "difficulty", "binary_label"]

# Consistent layout applied to every chart
_LAYOUT = dict(
    template="plotly_white",
    font=dict(family="Inter, system-ui, -apple-system, sans-serif", size=12, color="#374151"),
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=40, r=20, t=50, b=40),
    hoverlabel=dict(bgcolor="white", font_size=12, bordercolor="#e2e8f0"),
    title_font=dict(size=14, color="#0f172a", weight="bold"),
)

_COLORS = {"normal": "#4f86f7", "attack": "#ef4444"}


# ── summary ───────────────────────────────────────────────────────────────────

def basic_summary(df: pd.DataFrame) -> dict:
    return {
        "shape":          df.shape,
        "missing_total":  int(df.isna().sum().sum()),
        "missing_per_col": df.isna().sum().to_dict(),
        "duplicates":     int(df.duplicated().sum()),
        "dtypes":         df.dtypes.astype(str).to_dict(),
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
    top = label_distribution(df).head(15)
    fig = px.bar(
        top, x="label", y="count", color="binary",
        color_discrete_map=_COLORS,
        title="Traffic Label Distribution (top 15)",
        labels={"label": "Label", "count": "Count", "binary": "Type"},
    )
    fig.update_layout(**_LAYOUT, xaxis_tickangle=-35, showlegend=True)
    fig.update_traces(marker_line_width=0)
    return fig


def fig_binary_pie(df: pd.DataFrame) -> go.Figure:
    binary = binary_distribution(df)
    fig = px.pie(
        values=binary.values, names=binary.index,
        title="Normal vs Attack Split",
        color=binary.index,
        color_discrete_map=_COLORS,
        hole=0.45,
    )
    fig.update_layout(**_LAYOUT)
    fig.update_traces(textposition="outside", textinfo="percent+label")
    return fig


def fig_categorical_distributions(df: pd.DataFrame) -> go.Figure:
    palette = ["#4f86f7", "#f97316", "#10b981"]
    fig = make_subplots(rows=1, cols=3, subplot_titles=CATEGORICAL_COLUMNS)
    for i, col in enumerate(CATEGORICAL_COLUMNS, start=1):
        vc = df[col].value_counts().head(10)
        fig.add_trace(
            go.Bar(
                x=vc.index.tolist(), y=vc.values.tolist(),
                name=col, marker_color=palette[i - 1],
                marker_line_width=0,
            ),
            row=1, col=i,
        )
    fig.update_layout(**_LAYOUT, title="Categorical Feature Distributions (top 10 each)", showlegend=False)
    return fig


def fig_numeric_distributions(df: pd.DataFrame, n_cols: int = 4) -> go.Figure:
    num_cols = [
        c for c in df.columns
        if c not in CATEGORICAL_COLUMNS + DROP_COLUMNS and pd.api.types.is_numeric_dtype(df[c])
    ][:20]
    n_rows = int(np.ceil(len(num_cols) / n_cols))
    fig = make_subplots(rows=n_rows, cols=n_cols, subplot_titles=num_cols)
    for idx, col in enumerate(num_cols):
        r, c = divmod(idx, n_cols)
        fig.add_trace(
            go.Histogram(
                x=df[col], name=col, nbinsx=30,
                showlegend=False, marker_color="#4f86f7", marker_line_width=0,
            ),
            row=r + 1, col=c + 1,
        )
    fig.update_layout(**_LAYOUT, title="Numeric Feature Distributions", height=220 * n_rows)
    return fig


def fig_correlation_heatmap(df: pd.DataFrame, top_n: int = 20) -> go.Figure:
    num_df   = df.select_dtypes(include="number").drop(
        columns=[c for c in ["difficulty"] if c in df.columns]
    )
    top_cols = num_df.std().nlargest(top_n).index.tolist()
    corr     = num_df[top_cols].corr()
    fig = px.imshow(
        corr,
        color_continuous_scale="RdBu_r",
        zmin=-1, zmax=1,
        title=f"Correlation Heatmap — top {top_n} numeric features by variance",
        aspect="auto",
    )
    fig.update_layout(**_LAYOUT)
    fig.update_coloraxes(colorbar_thickness=14)
    return fig


def fig_attack_types(df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    attacks = (
        df[df["label"].str.strip().str.lower() != "normal"]["label"]
        .value_counts()
        .head(top_n)
    )
    fig = px.bar(
        x=attacks.values, y=attacks.index,
        orientation="h",
        title=f"Top {top_n} Attack Types",
        labels={"x": "Count", "y": "Attack Type"},
        color=attacks.values,
        color_continuous_scale=["#fca5a5", "#ef4444", "#991b1b"],
    )
    fig.update_layout(
        **_LAYOUT,
        yaxis={"categoryorder": "total ascending"},
        coloraxis_showscale=False,
    )
    fig.update_traces(marker_line_width=0)
    return fig


def fig_feature_by_binary_label(df: pd.DataFrame, feature: str) -> go.Figure:
    plot_df = df[[feature, "label"]].copy()
    plot_df["binary"] = plot_df["label"].apply(
        lambda x: "normal" if str(x).strip().lower() == "normal" else "attack"
    )
    fig = px.box(
        plot_df, x="binary", y=feature,
        color="binary",
        color_discrete_map=_COLORS,
        title=f"{feature} — normal vs attack",
        points=False,
    )
    fig.update_layout(**_LAYOUT)
    return fig
