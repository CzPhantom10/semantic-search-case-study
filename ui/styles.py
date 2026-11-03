"""Global visual system for the Streamlit application."""
import streamlit as st


def apply_styles():
    st.markdown('''<style>
:root{--ink:#17243b;--muted:#64748b;--line:#e2e8f0;--blue:#3157c8;--blue-soft:#edf2ff;--panel:#fff;--canvas:#f5f7fb;--green:#16836d}
html,body,[class*="css"]{font-family:Inter,"Segoe UI",sans-serif;color:var(--ink)}
.stApp{background:var(--canvas)}
[data-testid="stSidebar"]{background:#101c31;border-right:1px solid #24344e}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"]{color:#f4f7ff}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2{letter-spacing:-.035em;color:#fff}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"]{color:#a6b4ca}
[data-testid="stSidebar"] label{color:#e3eafa}
[data-testid="stMetric"]{background:var(--panel);border:1px solid var(--line);padding:17px 19px;border-radius:15px;box-shadow:0 4px 14px #233d6809}
[data-testid="stMetricLabel"]{color:var(--muted);font-weight:600}
[data-testid="stMetricValue"]{color:var(--ink);font-weight:750}
.hero{background:linear-gradient(112deg,#14233a 0%,#1c3766 60%,#3157a3 100%);padding:34px 38px;border-radius:20px;color:#fff;margin:0 0 24px;box-shadow:0 13px 30px #152a4a24}
.hero .eyebrow{font-size:.74rem;letter-spacing:.14em;text-transform:uppercase;color:#b9ccff;font-weight:750;margin-bottom:10px}
.hero h1{margin:0 0 9px;font-size:2.05rem;letter-spacing:-.045em;color:#fff}.hero p{margin:0;color:#e0e9ff;font-size:1.02rem;max-width:760px}
.page-head{padding:7px 0 14px}.page-head .eyebrow{font-size:.73rem;letter-spacing:.13em;text-transform:uppercase;color:var(--blue);font-weight:750}.page-head h1{font-size:1.85rem;letter-spacing:-.04em;color:var(--ink);margin:4px 0}.page-head p{color:var(--muted);margin:0}
.result{background:var(--panel);border:1px solid var(--line);border-radius:15px;padding:17px 19px;margin:12px 0;box-shadow:0 4px 14px #233d6808}
.result-head{display:flex;justify-content:space-between;gap:12px;align-items:center}.result-title{font-weight:700;color:#20345d}.score-pill{display:inline-block;padding:5px 9px;border-radius:999px;background:var(--blue-soft);color:#344da2;font-size:.78rem;font-weight:700;white-space:nowrap}
.result p{line-height:1.65;color:#34415a;margin:12px 0}.inventory{background:#fff;border:1px solid var(--line);border-radius:15px;padding:16px 18px;margin:14px 0}.inventory-title{font-size:1.02rem;font-weight:750;color:#20345d}.inventory-sub{color:var(--muted);font-size:.86rem;margin-top:3px}
mark{background:#fff0b8;color:#392f16;padding:1px 2px;border-radius:3px}
div[data-testid="stButton"]>button[kind="primary"]{background:var(--blue);border-color:var(--blue);border-radius:9px;font-weight:700}
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:12px;overflow:hidden}
</style>''',unsafe_allow_html=True)
