"""Streamlit interface for the keyword vs semantic retrieval case study."""
import hashlib, json, time, html, re
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
import config
from database.db_manager import Database, utcnow
from core.document_processor import extract_document
from core.chunker import chunk_pages
from core.embedding_engine import EmbeddingEngine
from core.vector_store import VectorStore
from core.keyword_engine import KeywordEngine
from core.evaluation import metrics, summarize
from core.semantic_engine import SemanticEngine

st.set_page_config(page_title='Case Study: Traditional Keyword Search vs AI-Powered Semantic Search Using ChromaDB',page_icon='🔎',layout='wide')
st.markdown('''<style>
:root{--ink:#17233e;--muted:#66738d;--line:#e2e8f2;--blue:#435fca;--panel:#fff;--canvas:#f4f6fb}
html,body,[class*="css"]{font-family:Inter,"Segoe UI",sans-serif;color:var(--ink)}
.stApp{background:var(--canvas)}
[data-testid="stSidebar"]{background:#fff;border-right:1px solid var(--line)}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2{letter-spacing:-.03em;color:#18274a}
[data-testid="stMetric"]{background:var(--panel);border:1px solid var(--line);padding:17px 19px;border-radius:16px;box-shadow:0 5px 18px #233d6810}
[data-testid="stMetricLabel"]{color:var(--muted);font-weight:600}
[data-testid="stMetricValue"]{color:var(--ink);font-weight:750}
.hero{background:linear-gradient(115deg,#14254a 0%,#263f7c 55%,#4b61b1 100%);padding:34px 38px;border-radius:22px;color:white;margin:0 0 25px;box-shadow:0 14px 32px #1d326526}
.hero .eyebrow{font-size:.76rem;letter-spacing:.14em;text-transform:uppercase;color:#c4d2ff;font-weight:700;margin-bottom:10px}
.hero h1{margin:0 0 9px;font-size:2.1rem;letter-spacing:-.045em;color:white}.hero p{margin:0;color:#e1e8ff;font-size:1.02rem;max-width:760px}
.page-head{padding:7px 0 14px}.page-head .eyebrow{font-size:.75rem;letter-spacing:.13em;text-transform:uppercase;color:var(--blue);font-weight:750}.page-head h1{font-size:1.85rem;letter-spacing:-.04em;color:var(--ink);margin:4px 0}.page-head p{color:var(--muted);margin:0}
.result{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:17px 19px;margin:12px 0;box-shadow:0 5px 16px #233d6808}
.result-head{display:flex;justify-content:space-between;gap:12px;align-items:center}.result-title{font-weight:700;color:#20345d}.score-pill{display:inline-block;padding:5px 9px;border-radius:999px;background:#eef2ff;color:#344da2;font-size:.78rem;font-weight:700;white-space:nowrap}
.result p{line-height:1.65;color:#34415a;margin:12px 0}.muted{color:var(--muted);font-size:.88rem}.inventory{background:#fff;border:1px solid var(--line);border-radius:16px;padding:16px 18px;margin:14px 0}.inventory-title{font-size:1.04rem;font-weight:750;color:#20345d}.inventory-sub{color:var(--muted);font-size:.86rem;margin-top:3px}
mark{background:#fff0b8;color:#392f16;padding:1px 2px;border-radius:3px}
div[data-testid="stButton"]>button[kind="primary"]{background:var(--blue);border-color:var(--blue);border-radius:10px;font-weight:700}
</style>''',unsafe_allow_html=True)
@st.cache_resource
def get_services():
    return Database(config.DB_PATH),EmbeddingEngine(config.MODEL_NAME,config.DEVICE),VectorStore(config.CHROMA_DIR)
try: db,emb,store=get_services()
except Exception as e:
    st.error(f'Could not initialize local search services: {e}');st.info('Install requirements.txt, then restart Streamlit.');st.stop()
with st.sidebar:
    st.markdown('## ◈ Search Lab');st.caption('DOCUMENT INTELLIGENCE')
    page=st.radio('Workspace',['Overview','Document Library','Upload Documents','Semantic Search','Keyword Search','Compare Search','Evaluation','Search History','Settings'],label_visibility='collapsed')
    st.divider();st.caption(f'Model: `{config.MODEL_NAME}`');st.caption('Local data stays in `data/`.')

def result_card(item,rank,semantic=False,query=''):
    meta=item.get('metadata',{});pg=f" · Page {meta.get('page_number')}" if meta.get('page_number') not in (None,'') else ''
    score=f"Cosine distance · {item['distance']:.4f}" if semantic else f"BM25 score · {item['score']:.4f}"
    name=html.escape(str(meta.get('document_name',meta.get('filename','Document'))));body=html.escape(str(item['text']));chunk_id=html.escape(str(item['chunk_id']))
    if not semantic:
        for term in set(query.split()):
            if len(term)>1:body=re.sub(re.escape(html.escape(term)),lambda m:f'<mark>{m.group(0)}</mark>',body,flags=re.IGNORECASE)
    st.markdown(f"<div class='result'><div class='result-head'><span class='result-title'>#{rank} · {name}{pg}</span><span class='score-pill'>{score}</span></div><p>{body}</p><code>{chunk_id}</code></div>",unsafe_allow_html=True)

def page_header(eyebrow,title,description):
    st.markdown(f"<div class='page-head'><div class='eyebrow'>{html.escape(eyebrow)}</div><h1>{html.escape(title)}</h1><p>{html.escape(description)}</p></div>",unsafe_allow_html=True)

def score_guide():
    with st.expander('How to read the scores',expanded=False):
        left,right=st.columns(2)
        left.markdown('''**BM25 score — higher ranks first**\n\nBM25 measures how strongly a passage matches the query words. It combines term frequency (how often a query word appears) with inverse document frequency (how distinctive that word is across your indexed chunks). It is a ranking score, **not a percentage or probability**. Interpret it within the same query and document collection; scores are not calibrated across different queries.''')
        right.markdown('''**Cosine distance — lower ranks first**\n\nThe app compares the query and passage embeddings using cosine distance. A distance near **0** means their vectors point in similar directions; larger values mean less similarity. With normalized vectors, the theoretical range is **0 to 2**. It is a geometric distance, **not a percentage, confidence, or probability**. Chroma returns the raw distance.''')

def render_upload_inventory():
    docs=[d for d in db.documents() if d.get('processing_status')=='indexed']
    st.markdown("<div class='inventory'><div class='inventory-title'>Your indexed documents</div><div class='inventory-sub'>This list updates from the local index. Manage or remove a document in Document Library.</div></div>",unsafe_allow_html=True)
    if not docs:
        st.info('No files indexed yet. Choose one or more files above to build your library.')
        return
    st.dataframe(pd.DataFrame([{'File':d['filename'],'Type':d['file_type'].upper(),'Status':'Indexed','Chunks':d['total_chunks'],'Pages':d['total_pages'] or '—','Added':d['upload_timestamp']} for d in docs]),use_container_width=True,hide_index=True)

def run_search(query,method,k):
    if method=='Keyword':
        start=time.perf_counter();items=KeywordEngine(db.chunks()).search(query,k);ms=(time.perf_counter()-start)*1000
    else:
        items,ms=SemanticEngine(emb,store).search(query,k)
        for x in items:x['metadata'].setdefault('filename',x['metadata'].get('document_name',''))
    packed=[{'chunk_id':x['chunk_id'],'text':x['text'],'score':x.get('score'),'distance':x.get('distance'),'metadata':x.get('metadata',{})} for x in items]
    db.record_search(query,method,ms,packed);return items,ms

if page=='Overview':
    counts=db.counts();st.markdown('<div class="hero"><div class="eyebrow">LOCAL DOCUMENT SEARCH</div><h1>Find the meaning behind your documents.</h1><p>Upload a library, search it two ways, and compare the evidence side by side.</p></div>',unsafe_allow_html=True)
    cols=st.columns(5)
    for col,label,val in zip(cols,['Indexed documents','Indexed chunks','Searches run','Vector store','Embedding model'],[counts['documents'],counts['chunks'],counts['searches'],'Connected',config.MODEL_NAME]):col.metric(label,val)
    st.subheader('Two ways to retrieve')
    a,b=st.columns(2)
    with a,st.container(border=True):
        st.markdown('### 01 · BM25 keyword search');st.write('Ranks passages by query-word matches. Often useful for exact names, labels, and phrases.')
        st.caption('Ranking score: higher is better')
    with b,st.container(border=True):
        st.markdown('### 02 · Semantic search');st.write('Compares locally generated meaning vectors. Can retrieve related wording even when exact terms differ.')
        st.caption('Cosine distance: lower is better')
    score_guide()
    st.subheader('Recent activity');h=db.history(8)
    if h:st.dataframe(pd.DataFrame(h)[['timestamp','query_text','search_method','latency_ms','result_count']],use_container_width=True,hide_index=True)
    else:st.caption('No searches yet. Add a document to begin.')
elif page=='Upload Documents':
    page_header('LIBRARY','Add documents','Upload files to create or expand your searchable library.')
    st.caption(f'PDF, DOCX, and TXT · Up to {config.MAX_UPLOAD_MB} MB per file · Scanned PDFs need OCR, which is not included.')
    files=st.file_uploader('Choose files',type=['pdf','docx','txt'],accept_multiple_files=True)
    if files and st.button('Index selected files',type='primary'):
        bar=st.progress(0)
        for n,f in enumerate(files):
            raw=f.getvalue();digest=hashlib.sha256(raw).hexdigest();suffix=Path(f.name).suffix.lower()
            if len(raw)>config.MAX_UPLOAD_MB*1024*1024:st.error(f'{f.name}: exceeds size limit');continue
            if any(d.get('file_hash')==digest for d in db.documents()):st.warning(f'{f.name}: identical file already indexed');continue
            docid=hashlib.sha256((digest+f.name).encode()).hexdigest()[:24];dest=config.UPLOAD_DIR/f'{docid}{suffix}';dest.write_bytes(raw);ts=utcnow()
            try:
                pages=extract_document(dest);chunks=chunk_pages(pages,docid,f.name,ts,config.CHUNK_SIZE,config.CHUNK_OVERLAP)
                if not chunks:raise ValueError('No text chunks were produced.')
                db.add_document({'document_id':docid,'filename':f.name,'file_type':suffix[1:],'upload_timestamp':ts,'processing_status':'processing','file_hash':digest})
                vectors=emb.encode([x['text'] for x in chunks]);store.upsert(chunks,vectors);db.add_chunks(chunks)
                db.set_document_status(docid,'indexed',sum(bool(p.get('text','').strip()) for p in pages),len(chunks));st.success(f'Indexed {f.name}: {len(chunks)} chunks')
            except Exception as e:
                if any(d['document_id']==docid for d in db.documents()):db.delete_document(docid)
                try:store.delete_document(docid)
                except Exception:pass
                dest.unlink(missing_ok=True);st.error(f'{f.name}: {e}')
            bar.progress((n+1)/len(files))
    render_upload_inventory()
elif page=='Document Library':
    page_header('LIBRARY','Document library','Review indexed files and remove documents you no longer need.')
    docs=db.documents()
    if not docs:st.info('No documents indexed yet. Upload a PDF, DOCX or TXT file to get started.')
    for d in docs:
        with st.container(border=True):
            left,right=st.columns([5,1]);left.markdown(f"**{d['filename']}** · `{d['processing_status']}`");left.caption(f"{d['total_chunks']} chunks · {d['total_pages']} pages · added {d['upload_timestamp']}")
            if right.button('Delete',key=f"del-{d['document_id']}"):
                store.delete_document(d['document_id']);db.delete_document(d['document_id']);(config.UPLOAD_DIR/f"{d['document_id']}.{d['file_type']}").unlink(missing_ok=True);st.rerun()
    if docs:st.caption('To re-index, delete and upload the updated file. Identical contents are detected by SHA-256.')
elif page in ('Semantic Search','Keyword Search','Compare Search'):
    titles={'Semantic Search':('SEMANTIC RETRIEVAL','Search by meaning','Find passages related to your question, even when wording differs.'),'Keyword Search':('LEXICAL RETRIEVAL','Search by keywords','Find passages with the same important terms as your query.'),'Compare Search':('SIDE-BY-SIDE','Compare methods','Run one query against the same indexed chunks using both ranking methods.')}
    eyebrow,title,description=titles[page];page_header(eyebrow,title,description)
    score_guide()
    query=st.text_input('Your query',placeholder='Example: How can I protect my computer from hackers?');k=st.slider('Results per method',1,20,config.DEFAULT_TOP_K)
    if st.button('Search',type='primary',disabled=not bool(query.strip())):
        if not db.chunks():st.warning('Index a document before searching.')
        elif page=='Compare Search':
            a,b=st.columns(2)
            for col,method in ((a,'Keyword'),(b,'Semantic')):
                with col:
                    st.subheader('BM25 · Keyword' if method=='Keyword' else 'Vector · Semantic');items,ms=run_search(query,method,k)
                    st.caption(f'Retrieval: {ms:.2f} ms'+(' · query embedding excluded' if method=='Semantic' else ''))
                    if items:
                        for i,r in enumerate(items,1):result_card(r,i,method=='Semantic',query)
                    else:st.info('No matching results.')
        else:
            method='Semantic' if page=='Semantic Search' else 'Keyword';items,ms=run_search(query,method,k)
            st.caption(f'Retrieval: {ms:.2f} ms'+(' · query embedding excluded' if method=='Semantic' else ''))
            if items:
                for i,r in enumerate(items,1):result_card(r,i,method=='Semantic',query)
            else:st.info('No matching results.')
elif page=='Evaluation':
    st.markdown('## Evaluation workbench');st.caption('Only human relevance judgments count. No judgments means no scores. Latency excludes model initialization and indexing; semantic query embedding is excluded.')
    with st.expander('Create test query'):
        with st.form('new_query'):
            q=st.text_input('Query');cat=st.text_input('Category');expected=st.text_input('Expected relevant information');ok=st.form_submit_button('Save query')
            if ok and q.strip():db.add_query(q,cat,expected);st.success('Saved');st.rerun()
    queries=db.queries();chunks=db.chunks()
    if queries:
        selected=st.selectbox('Choose query',queries,format_func=lambda x:f"Q{x['query_id']}: {x['query_text']}")
        if chunks:
            opts={f"{c['filename']} · {c.get('page_number') or 'no page'} · {c['text'][:100]}…":c for c in chunks};judged=db.judgments(selected['query_id'])
            chosen=st.multiselect('Relevant chunks (selected chunks receive grade 2)',list(opts),default=[label for label,c in opts.items() if judged.get(c['chunk_id'],0)>0])
            if st.button('Save relevance judgments'):
                active={opts[x]['chunk_id'] for x in chosen}
                for c in chunks:db.save_judgment(selected['query_id'],c['chunk_id'],2 if c['chunk_id'] in active else 0)
                st.success('Judgments saved.')
            if st.button('Run paired evaluation'):
                grades=db.judgments(selected['query_id'])
                if not any(grades.values()):st.warning('Save at least one relevant chunk first.')
                else:
                    rows=[]
                    experiment_id=db.create_experiment(f"Paired evaluation: {selected['query_text'][:60]}",config.MODEL_NAME,{'top_k':config.DEFAULT_TOP_K,'chunk_size_words':config.CHUNK_SIZE,'chunk_overlap_words':config.CHUNK_OVERLAP,'latency_runs':config.LATENCY_RUNS,'distance_metric':'cosine'})
                    for method in ('Keyword','Semantic'):
                        measured=[]; found=[]
                        for _ in range(config.LATENCY_RUNS):
                            found,ms=run_search(selected['query_text'],method,config.DEFAULT_TOP_K);measured.append(ms)
                        m=metrics([x['chunk_id'] for x in found],grades,config.DEFAULT_TOP_K)
                        m['latency_ms']=sum(measured)/len(measured);m['latency_std_ms']=pd.Series(measured).std(ddof=0);db.save_evaluation(experiment_id,selected['query_id'],method,m)
                        rows.append({'query':selected['query_text'],'method':method,**m})
                    st.session_state['eval_rows']=st.session_state.get('eval_rows',[])+rows
    rows=db.evaluation_rows()
    if rows:
        df=pd.DataFrame(rows);st.dataframe(df,use_container_width=True,hide_index=True);means=df.groupby('method',as_index=False).mean(numeric_only=True)
        metric=st.selectbox('Quality metric',['precision_at_k','recall_at_k','mrr','ndcg_at_k'],format_func=lambda x:{'precision_at_k':'Precision@K','recall_at_k':'Recall@K','mrr':'MRR','ndcg_at_k':'NDCG@K'}[x]);a,b=st.columns(2)
        with a:st.plotly_chart(px.bar(means,x='method',y=metric,title=metric.replace('_',' ').upper(),range_y=[0,1]),use_container_width=True)
        with b:st.plotly_chart(px.bar(means,x='method',y='latency_ms',error_y='latency_std_ms',title=f'Mean retrieval latency ± SD ({config.LATENCY_RUNS} runs)'),use_container_width=True)
        st.write(summarize(rows));st.download_button('Export evaluation CSV',df.to_csv(index=False),'evaluation_results.csv','text/csv')
    else:st.info('Create a query, label relevant chunks, and run paired evaluation to populate this dashboard.')
elif page=='Search History':
    st.markdown('## Search history');rows=db.history()
    if rows:
        df=pd.DataFrame(rows);st.dataframe(df[['timestamp','query_text','search_method','latency_ms','result_count']],use_container_width=True,hide_index=True)
        pick=st.selectbox('Revisit a search',rows,format_func=lambda x:f"{x['search_method']} · {x['query_text']}")
        with st.expander('Saved results'):st.json(json.loads(pick['results_json']))
        st.download_button('Export history CSV',df.drop(columns=['results_json']).to_csv(index=False),'search_history.csv','text/csv')
    else:st.caption('Search history will appear after your first query.')
elif page=='Settings':
    st.markdown('## Settings');st.json({'embedding_model':config.MODEL_NAME,'embedding_dimensions':emb.dimension,'device':str(getattr(emb.model,'device','auto')),'chunk_size_words':config.CHUNK_SIZE,'chunk_overlap_words':config.CHUNK_OVERLAP,'default_top_k':config.DEFAULT_TOP_K,'latency_runs':config.LATENCY_RUNS,'distance_metric':'cosine','chroma_path':str(config.CHROMA_DIR),'sqlite_path':str(config.DB_PATH)})
    st.caption('Configure SEMSEARCH_MODEL, SEMSEARCH_CHUNK_SIZE, SEMSEARCH_CHUNK_OVERLAP, SEMSEARCH_TOP_K, SEMSEARCH_LATENCY_RUNS or SEMSEARCH_DEVICE, then restart. Re-index after changing model or chunk settings.')
