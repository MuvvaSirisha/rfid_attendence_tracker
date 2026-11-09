"""
SmartAttend — Shared UI helpers
Reusable HTML components for consistent styling across all pages.
"""

import streamlit as st

# ── Design tokens ──────────────────────────────────────────────────────────────
NAVY    = "#1B2A4A"
BLUE    = "#2563EB"
GREEN   = "#16A34A"
AMBER   = "#D97706"
RED     = "#DC2626"
GRAY    = "#64748B"
LIGHT   = "#F4F6FA"


GLOBAL_CSS = """
<style>
/* ── Hide default Streamlit multi-page auto-navigation ── */
[data-testid="stSidebarNav"] { display: none !important; }

/* ── Layout ── */
[data-testid="stAppViewContainer"] { background: #F4F6FA; }
[data-testid="stSidebar"] {
    background: #1B2A4A !important;
}
[data-testid="stSidebar"] * { color: #E2E8F0 !important; }
[data-testid="stSidebar"] .stRadio label { font-size: 0.95rem; }
[data-testid="stSidebar"] hr { border-color: #334155 !important; }
[data-testid="stSidebarContent"] { padding-top: 1rem; }

/* ── Cards ── */
.sa-card {
    background: #FFFFFF;
    border-radius: 12px;
    padding: 20px 24px;
    box-shadow: 0 1px 6px rgba(0,0,0,0.07);
    border: 1px solid #E2E8F0;
}

/* ── Metric cards ── */
.metric-card {
    background: #FFFFFF;
    border-radius: 12px;
    padding: 22px 20px 18px;
    box-shadow: 0 1px 6px rgba(0,0,0,0.08);
    border: 1px solid #E2E8F0;
    display: flex;
    align-items: center;
    gap: 16px;
    min-height: 90px;
}
.metric-icon {
    font-size: 2.2rem;
    line-height: 1;
    min-width: 48px;
    text-align: center;
}
.metric-label {
    font-size: 0.78rem;
    color: #64748B;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 2px;
}
.metric-value {
    font-size: 2rem;
    font-weight: 700;
    line-height: 1.1;
}
.metric-sub {
    font-size: 0.75rem;
    color: #94A3B8;
    margin-top: 2px;
}

/* ── Status badges ── */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
}
.badge-present { background: #DCFCE7; color: #15803D; }
.badge-late    { background: #FEF3C7; color: #B45309; }
.badge-absent  { background: #FEE2E2; color: #B91C1C; }
.badge-online  { background: #DCFCE7; color: #15803D; }
.badge-offline { background: #FEE2E2; color: #B91C1C; }

/* ── Scan result boxes ── */
.scan-success {
    background: #F0FDF4;
    border: 2px solid #16A34A;
    border-radius: 14px;
    padding: 28px 32px;
    text-align: center;
    margin-bottom: 20px;
}
.scan-duplicate {
    background: #FFFBEB;
    border: 2px solid #D97706;
    border-radius: 14px;
    padding: 28px 32px;
    text-align: center;
    margin-bottom: 20px;
}
.scan-unknown {
    background: #FFF1F2;
    border: 2px solid #DC2626;
    border-radius: 14px;
    padding: 28px 32px;
    text-align: center;
    margin-bottom: 20px;
}
.scan-waiting {
    background: #EFF6FF;
    border: 2px dashed #3B82F6;
    border-radius: 14px;
    padding: 36px;
    text-align: center;
    margin-bottom: 20px;
}

/* ── Section headers ── */
.section-header {
    font-size: 1.1rem;
    font-weight: 700;
    color: #1B2A4A;
    border-left: 4px solid #2563EB;
    padding-left: 10px;
    margin: 24px 0 12px;
}

/* ── Tables ── */
[data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; }

/* ── Sidebar title ── */
.sidebar-title {
    font-size: 1.3rem;
    font-weight: 800;
    color: #FFFFFF !important;
    letter-spacing: -0.01em;
}
.sidebar-sub {
    font-size: 0.78rem;
    color: #94A3B8 !important;
    margin-top: -4px;
    margin-bottom: 8px;
}

/* ── Page title ── */
.page-title {
    font-size: 1.7rem;
    font-weight: 800;
    color: #1B2A4A;
    margin-bottom: 2px;
}
.page-sub {
    font-size: 0.9rem;
    color: #64748B;
    margin-bottom: 24px;
}
</style>
"""


def inject_css():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def metric_card(icon: str, label: str, value, color: str = "#1B2A4A", sub: str = ""):
    sub_html = f'<div class="metric-sub">{sub}</div>' if sub else ""
    return f"""
    <div class="metric-card">
        <div class="metric-icon">{icon}</div>
        <div>
            <div class="metric-label">{label}</div>
            <div class="metric-value" style="color:{color};">{value}</div>
            {sub_html}
        </div>
    </div>"""


def status_badge(status: str) -> str:
    css = {
        "Present": "badge-present",
        "Late":    "badge-late",
        "Absent":  "badge-absent",
        "Online":  "badge-online",
        "Offline": "badge-offline",
    }.get(status, "badge")
    return f'<span class="badge {css}">{status}</span>'


def section_header(title: str):
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)


def page_header(title: str, subtitle: str = ""):
    sub_html = f'<div class="page-sub">{subtitle}</div>' if subtitle else ""
    st.markdown(f'<div class="page-title">{title}</div>{sub_html}', unsafe_allow_html=True)


def card(content_html: str):
    st.markdown(f'<div class="sa-card">{content_html}</div>', unsafe_allow_html=True)


def style_table(styler, style_fn, subset=None):
    """
    Apply cell-level styling safely across pandas versions.
    Pandas >= 2.1 removed Styler.applymap in favor of Styler.map.
    """
    if hasattr(styler, "map"):
        return styler.map(style_fn, subset=subset)
    elif hasattr(styler, "applymap"):
        return styler.applymap(style_fn, subset=subset)
    return styler

