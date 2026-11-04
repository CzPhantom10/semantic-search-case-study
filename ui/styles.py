"""Warm, minimal glass-inspired visual system for the Streamlit workspace."""
import streamlit as st


def apply_styles():
    st.markdown('''<style>
:root{--ink:#24221e;--muted:#77746d;--line:rgba(95,83,62,.14);--accent:#917a58;--accent-soft:#eee8dd;--panel:rgba(255,255,255,.72);--canvas:#f3f1ec}
html,body,[class*="css"]{font-family:Inter,"Segoe UI",sans-serif;color:var(--ink)}
.stApp{background:radial-gradient(ellipse at 12% 0%,#faf9f6 0%,var(--canvas) 58%,#eeece6 100%);background-attachment:fixed}
[data-testid="stAppViewBlockContainer"]{max-width:1440px;padding-top:1.1rem}
[data-testid="stSidebar"]{background:rgba(250,249,246,.88);border-right:1px solid var(--line);backdrop-filter:blur(18px);min-width:250px}
[data-testid="stSidebar"]>div:first-child{padding-top:1.35rem}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"]{color:var(--ink)}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2{letter-spacing:-.035em;color:var(--ink)}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"]{color:var(--muted)}
[data-testid="stSidebar"] label{color:var(--ink)}
[data-testid="stSidebar"] [role="radiogroup"] label{border-radius:9px;padding:5px 8px;transition:background .18s ease,color .18s ease}
[data-testid="stSidebar"] [role="radiogroup"] label:hover{background:rgba(145,122,88,.09)}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){background:rgba(145,122,88,.13);font-weight:650}
.hero{background:rgba(255,255,255,.68);border:1px solid rgba(255,255,255,.9);padding:32px 36px;border-radius:18px;color:var(--ink);margin:0 0 20px;box-shadow:0 10px 28px rgba(47,41,32,.055);backdrop-filter:blur(18px)}
.hero .eyebrow{font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;color:var(--accent);font-weight:750;margin-bottom:9px}
.hero h1{margin:0 0 9px;font-size:2rem;letter-spacing:-.04em;color:var(--ink)}.hero p{margin:0;color:var(--muted);font-size:1rem;max-width:760px;line-height:1.55}
.page-head{padding:7px 0 14px}.page-head .eyebrow{font-size:.72rem;letter-spacing:.13em;text-transform:uppercase;color:var(--accent);font-weight:750}.page-head h1{font-size:1.85rem;letter-spacing:-.04em;color:var(--ink);margin:4px 0}.page-head p{color:var(--muted);margin:0}
[data-testid="stMetric"]{background:var(--panel);border:1px solid rgba(255,255,255,.9);padding:17px 19px;border-radius:16px;box-shadow:0 6px 20px rgba(47,41,32,.045);backdrop-filter:blur(16px);transition:transform .18s ease,box-shadow .18s ease}
[data-testid="stMetric"]:hover{transform:translateY(-2px);box-shadow:0 10px 25px rgba(47,41,32,.08)}
[data-testid="stMetricLabel"]{color:var(--muted);font-weight:600}[data-testid="stMetricValue"]{color:var(--ink);font-weight:750}
[data-testid="stVerticalBlockBorderWrapper"]{border-color:var(--line)!important;border-radius:16px!important;background:rgba(255,255,255,.54);backdrop-filter:blur(14px);box-shadow:0 5px 18px rgba(47,41,32,.035);transition:border-color .18s ease,box-shadow .18s ease}
[data-testid="stVerticalBlockBorderWrapper"]:hover{border-color:rgba(145,122,88,.32)!important;box-shadow:0 8px 22px rgba(47,41,32,.06)}
.result{background:var(--panel);border:1px solid rgba(255,255,255,.9);border-radius:16px;padding:17px 19px;margin:12px 0;box-shadow:0 5px 18px rgba(47,41,32,.045);backdrop-filter:blur(14px)}
.result-head{display:flex;justify-content:space-between;gap:12px;align-items:center}.result-title{font-weight:700;color:var(--ink)}.score-pill{display:inline-block;padding:5px 9px;border-radius:999px;background:var(--accent-soft);color:#66563e;font-size:.78rem;font-weight:700;white-space:nowrap}
.result p{line-height:1.65;color:#484640;margin:12px 0}.inventory{background:var(--panel);border:1px solid rgba(255,255,255,.9);border-radius:16px;padding:16px 18px;margin:14px 0;backdrop-filter:blur(14px)}.inventory-title{font-size:1.02rem;font-weight:750;color:var(--ink)}.inventory-sub{color:var(--muted);font-size:.86rem;margin-top:3px}
mark{background:#eee6d7;color:#443a2a;padding:1px 2px;border-radius:3px}
div[data-testid="stButton"]>button{border-radius:10px;transition:transform .16s ease,box-shadow .16s ease,background .16s ease}
div[data-testid="stButton"]>button:hover{transform:translateY(-1px);box-shadow:0 6px 14px rgba(47,41,32,.1)}
div[data-testid="stButton"]>button[kind="primary"]{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:700}
[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea,[data-testid="stSelectbox"] div[data-baseweb="select"]>div{border-radius:10px;border-color:var(--line);background:rgba(255,255,255,.72)}
[data-testid="stTextInput"] input:focus,[data-testid="stTextArea"] textarea:focus{border-color:rgba(145,122,88,.6);box-shadow:0 0 0 2px rgba(145,122,88,.12)}
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:13px;overflow:hidden;background:var(--panel)}
.app-brand{font-size:1.22rem;font-weight:760;letter-spacing:-.035em;color:var(--ink);padding-top:.4rem}.app-brand-mark{color:var(--accent)}
.app-brand-caption{font-size:.72rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-top:.22rem}
.workflow-card{min-height:190px}
@media(max-width:700px){
  .hero{padding:24px 20px;border-radius:15px}.hero h1{font-size:1.65rem}
  [data-testid="stHorizontalBlock"]{flex-wrap:wrap;gap:.7rem}
  [data-testid="stHorizontalBlock"]>[data-testid="column"]{flex:1 1 100%!important;width:100%!important;min-width:100%!important}
  [data-testid="stMetric"]{padding:14px 16px}.page-head h1{font-size:1.55rem}
}
</style>''',unsafe_allow_html=True)
