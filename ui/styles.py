"""Global visual system for the Streamlit application."""
import streamlit as st


def apply_styles():
    st.markdown('''<style>
:root{--ink:#18243a;--muted:#66758b;--line:#e5e9f0;--blue:#3c5fc8;--blue-soft:#eef2ff;--panel:#fff;--canvas:#f7f8fb;--green:#16836d}
html,body,[class*="css"]{font-family:Inter,"Segoe UI",sans-serif;color:var(--ink)}
.stApp{background:var(--canvas)}
[data-testid="stAppViewBlockContainer"]{max-width:1440px;padding-top:1.2rem}
[data-testid="stMetric"]{background:var(--panel);border:1px solid var(--line);padding:17px 19px;border-radius:13px;box-shadow:0 2px 8px #233d6807}
[data-testid="stMetricLabel"]{color:var(--muted);font-weight:600}
[data-testid="stMetricValue"]{color:var(--ink);font-weight:750}
.hero{background:#fff;border:1px solid var(--line);padding:32px 36px;border-radius:15px;color:var(--ink);margin:0 0 20px;box-shadow:0 2px 8px #233d6806}
.hero .eyebrow{font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;color:var(--blue);font-weight:750;margin-bottom:9px}
.hero h1{margin:0 0 9px;font-size:2rem;letter-spacing:-.04em;color:var(--ink)}.hero p{margin:0;color:var(--muted);font-size:1rem;max-width:760px}
.page-head{padding:7px 0 14px}.page-head .eyebrow{font-size:.73rem;letter-spacing:.13em;text-transform:uppercase;color:var(--blue);font-weight:750}.page-head h1{font-size:1.85rem;letter-spacing:-.04em;color:var(--ink);margin:4px 0}.page-head p{color:var(--muted);margin:0}
.result{background:var(--panel);border:1px solid var(--line);border-radius:15px;padding:17px 19px;margin:12px 0;box-shadow:0 4px 14px #233d6808}
.result-head{display:flex;justify-content:space-between;gap:12px;align-items:center}.result-title{font-weight:700;color:#20345d}.score-pill{display:inline-block;padding:5px 9px;border-radius:999px;background:var(--blue-soft);color:#344da2;font-size:.78rem;font-weight:700;white-space:nowrap}
.result p{line-height:1.65;color:#34415a;margin:12px 0}.inventory{background:#fff;border:1px solid var(--line);border-radius:15px;padding:16px 18px;margin:14px 0}.inventory-title{font-size:1.02rem;font-weight:750;color:#20345d}.inventory-sub{color:var(--muted);font-size:.86rem;margin-top:3px}
mark{background:#fff0b8;color:#392f16;padding:1px 2px;border-radius:3px}
div[data-testid="stButton"]>button[kind="primary"]{background:var(--blue);border-color:var(--blue);border-radius:9px;font-weight:700}
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:12px;overflow:hidden}
.app-brand{font-size:1.22rem;font-weight:760;letter-spacing:-.035em;color:var(--ink);padding-top:.4rem}
.app-brand-mark{color:var(--blue)}
.app-brand-caption{font-size:.72rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-top:.22rem}
@media(max-width:700px){
  .hero{padding:24px 20px;border-radius:13px}
  .hero h1{font-size:1.65rem}
  [data-testid="stHorizontalBlock"]{flex-wrap:wrap;gap:.7rem}
  [data-testid="stHorizontalBlock"]>[data-testid="column"]{flex:1 1 100%!important;width:100%!important;min-width:100%!important}
  [data-testid="stMetric"]{padding:14px 16px}
  .page-head h1{font-size:1.55rem}
}
</style>''',unsafe_allow_html=True)
