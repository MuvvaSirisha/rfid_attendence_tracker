"""
SmartAttend — Shared Plotly chart builders
All charts use a consistent white-card style with navy/blue palette.
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Design tokens
COLORS = {
    "Present": "#16A34A",
    "Late":    "#D97706",
    "Absent":  "#DC2626",
}
NAVY       = "#1B2A4A"
BLUE       = "#2563EB"
LIGHT_GRID = "rgba(0,0,0,0.05)"

_BASE_PAPER  = "rgba(0,0,0,0)"
_BASE_PLOT   = "rgba(0,0,0,0)"
_BASE_FONT   = dict(family="system-ui, sans-serif", color="#374151")
_BASE_MARGIN = dict(l=0, r=0, t=20, b=0)
_BASE_LEGEND = dict(orientation="h", y=-0.15)


def _apply_base(fig: go.Figure, **extra):
    """Apply shared layout settings, then merge any extras."""
    fig.update_layout(
        paper_bgcolor=_BASE_PAPER,
        plot_bgcolor=_BASE_PLOT,
        font=_BASE_FONT,
        margin=_BASE_MARGIN,
        legend=_BASE_LEGEND,
        **extra,
    )


def attendance_bar_chart(daily_df: pd.DataFrame, title: str = "") -> go.Figure:
    """Stacked bar: Present/Late/Absent per day."""
    if daily_df.empty:
        fig = go.Figure()
        _apply_base(fig, title=title or "No data")
        return fig

    fig = px.bar(
        daily_df,
        x="date", y="count", color="status", barmode="stack",
        color_discrete_map=COLORS,
        labels={"date": "Date", "count": "Students", "status": ""},
        title=title,
    )
    _apply_base(fig,
        xaxis=dict(showgrid=False, tickangle=-30),
        yaxis=dict(gridcolor=LIGHT_GRID, zeroline=False),
        bargap=0.25,
    )
    return fig


def attendance_donut_chart(present: int, late: int, absent: int) -> go.Figure:
    """Donut chart for today's attendance distribution."""
    labels = ["Present", "Late", "Absent"]
    values = [present, late, absent]
    colors = [COLORS["Present"], COLORS["Late"], COLORS["Absent"]]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.6,
        marker=dict(colors=colors, line=dict(color="#FFFFFF", width=2)),
        textinfo="percent+label",
        insidetextorientation="radial",
    )])
    fig.update_layout(
        paper_bgcolor=_BASE_PAPER,
        plot_bgcolor=_BASE_PLOT,
        font=_BASE_FONT,
        showlegend=True,
        legend=dict(orientation="h", y=-0.1),
        margin=dict(l=0, r=0, t=10, b=10),
        annotations=[dict(
            text=f"<b>{present + late}</b><br><span style='font-size:10px'>Present</span>",
            x=0.5, y=0.5, font_size=18, showarrow=False,
        )],
    )
    return fig


def student_pct_bar_chart(df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart of per-student attendance %."""
    if df.empty:
        return go.Figure()
    df_sorted = df.sort_values("attendance_pct")
    colors = df_sorted["attendance_pct"].apply(
        lambda p: COLORS["Absent"] if p < 60 else (COLORS["Late"] if p < 75 else COLORS["Present"])
    )
    fig = go.Figure(go.Bar(
        x=df_sorted["attendance_pct"],
        y=df_sorted["name"] + " (" + df_sorted["roll"] + ")",
        orientation="h",
        marker_color=colors,
        text=df_sorted["attendance_pct"].astype(str) + "%",
        textposition="outside",
        cliponaxis=False,
    ))
    _apply_base(fig,
        xaxis=dict(range=[0, 110], showgrid=True, gridcolor=LIGHT_GRID,
                   title="Attendance %", ticksuffix="%"),
        yaxis=dict(showgrid=False),
        height=max(300, len(df) * 32),
    )
    return fig


def dept_bar_chart(df: pd.DataFrame) -> go.Figure:
    """Bar chart of dept-wise attendance %."""
    if df.empty:
        return go.Figure()
    fig = px.bar(
        df, x="dept", y="pct", text="pct",
        color="pct",
        color_continuous_scale=["#DC2626", "#D97706", "#16A34A"],
        range_color=[50, 100],
        labels={"dept": "Department", "pct": "Attendance %"},
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    _apply_base(fig,
        coloraxis_showscale=False,
        yaxis=dict(range=[0, 110], ticksuffix="%", gridcolor=LIGHT_GRID),
        xaxis=dict(showgrid=False),
    )
    return fig


def monthly_trend_chart(df: pd.DataFrame) -> go.Figure:
    """Line/area chart of monthly attendance counts."""
    if df.empty:
        return go.Figure()
    pivot = df.pivot_table(
        index="month", columns="status", values="count", fill_value=0
    ).reset_index()

    fig = go.Figure()
    for status in ["Present", "Late", "Absent"]:
        if status in pivot.columns:
            fig.add_trace(go.Scatter(
                x=pivot["month"],
                y=pivot[status],
                mode="lines+markers",
                name=status,
                line=dict(color=COLORS[status], width=2.5),
                fill="tozeroy" if status == "Present" else "none",
                fillcolor="rgba(22,163,74,0.08)",
            ))
    _apply_base(fig,
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor=LIGHT_GRID, zeroline=False),
    )
    return fig
