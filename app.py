"""Semantic Search Studio: a local document retrieval application."""
import hashlib, json
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
import config
from ui.components import page_header, render_navigation, render_upload_inventory, result_card, score_guide, set_workspace_page
from ui.styles import apply_styles
from services.search_service import run_search
from database.db_manager import Database, utcnow
from core.document_processor import extract_document
from core.chunker import chunk_pages
from core.embedding_engine import EmbeddingEngine
from core.vector_store import VectorStore
from core.evaluation import metrics, summarize

st.set_page_config(page_title='Semantic Search Studio',page_icon='🔎',layout='wide',initial_sidebar_state='collapsed')
if 'studio_navigation_page' not in st.session_state:
    st.session_state['studio_navigation_page']='Overview'
apply_styles()
@st.cache_resource
def get_services():
    return Database(config.DB_PATH),EmbeddingEngine(config.MODEL_NAME,config.DEVICE),VectorStore(config.CHROMA_DIR)
try: db,emb,store=get_services()
except Exception as e:
    st.error(f'Could not initialize local search services: {e}');st.info('Install requirements.txt, then restart Streamlit.');st.stop()
header_brand,header_nav=st.columns([2.2,1])
with header_brand:
    st.markdown("<div class='app-brand'><span class='app-brand-mark'>◈</span> Semantic Search Studio</div><div class='app-brand-caption'>Local document workspace</div>",unsafe_allow_html=True)
with header_nav:
    page=render_navigation()
st.divider()

if page=='Overview':
    counts=db.counts();st.markdown('<div class="hero"><div class="eyebrow">DOCUMENT SEARCH WORKSPACE</div><h1>Search your documents.</h1><p>Upload a library, find passages with BM25 or semantic similarity, and compare where each method helps.</p></div>',unsafe_allow_html=True)
    st.button('Add documents' if counts['documents']==0 else 'Add more documents',type='primary',
        on_click=set_workspace_page,args=('Upload Documents',))
    if counts['documents']==0:
        st.caption('Your library is empty. Add PDF, DOCX, or TXT files to get started.')
    cols=st.columns(3)
    for col,label,val in zip(cols,['Documents','Chunks','Searches'],[counts['documents'],counts['chunks'],counts['searches']]):col.metric(label,val)
    st.caption(f"Vector store connected · {config.MODEL_NAME} · local inference")
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
    if h:
        activity=pd.DataFrame(h).rename(columns={'timestamp':'Time','query_text':'Query','search_method':'Method','result_count':'Results'})
        activity['Measured time (ms)']=activity['end_to_end_ms'].fillna(activity['latency_ms'])
        activity['Timing scope']=activity.apply(lambda row:'End to end' if pd.notna(row['end_to_end_ms']) else ('Legacy retrieval only' if row['search_method']=='Semantic' else 'Legacy BM25 index + scoring'),axis=1)
        st.dataframe(activity[['Time','Query','Method','Measured time (ms)','Timing scope','Results']],use_container_width=True,hide_index=True)
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
    render_upload_inventory(db)
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
                    st.subheader('BM25 · Keyword' if method=='Keyword' else 'Vector · Semantic');items,timing=run_search(db,emb,store,query,method,k)
                    st.caption(f"End to end: {timing['end_to_end_ms']:.2f} ms · Retrieval only: {timing['retrieval_ms']:.2f} ms")
                    if items:
                        for i,r in enumerate(items,1):result_card(r,i,method=='Semantic',query)
                    else:st.info('No matching results.')
        else:
            method='Semantic' if page=='Semantic Search' else 'Keyword';items,timing=run_search(db,emb,store,query,method,k)
            st.caption(f"End to end: {timing['end_to_end_ms']:.2f} ms · Retrieval only: {timing['retrieval_ms']:.2f} ms")
            if items:
                for i,r in enumerate(items,1):result_card(r,i,method=='Semantic',query)
            else:st.info('No matching results.')
elif page=='Evaluation':
    st.markdown('## Evaluation workbench');st.caption('Build a repeatable comparison from your indexed corpus, queries, and explicit relevance grades. Model loading and shared SQLite chunk loading are excluded from query timing.')
    with st.expander('Create test query'):
        with st.form('new_query'):
            q=st.text_input('Query');cat=st.text_input('Category');expected=st.text_input('Expected relevant information');ok=st.form_submit_button('Save query')
            if ok and q.strip():db.add_query(q,cat,expected);st.success('Saved');st.rerun()
    queries=db.queries();chunks=db.chunks();pending_grades=None;unsaved_grades=False
    if queries:
        selected=st.selectbox('Choose query',queries,format_func=lambda x:f"Q{x['query_id']} · {x.get('category') or 'Uncategorized'}: {x['query_text']}")
        if chunks:
            judged=db.judgments(selected['query_id'])
            grade_labels={None:'Unjudged',0:'0 · Not relevant',1:'1 · Marginally relevant',2:'2 · Relevant',3:'3 · Highly relevant'}
            label_grades={label:grade for grade,label in grade_labels.items()}
            judgment_rows=[]
            for chunk in chunks:
                page_number=chunk.get('page_number')
                judgment_rows.append({'chunk_id':chunk['chunk_id'],'document':chunk['filename'],
                    'page':page_number if page_number not in (None,'') else '—',
                    'passage':chunk['text'],'relevance':grade_labels.get(judged.get(chunk['chunk_id']))})
            edited=st.data_editor(pd.DataFrame(judgment_rows),hide_index=True,use_container_width=True,
                disabled=['chunk_id','document','page','passage'],key=f"judgments-{selected['query_id']}",
                column_config={'passage':st.column_config.TextColumn('Passage',width='large'),
                    'relevance':st.column_config.SelectboxColumn('Relevance grade',
                        options=list(label_grades),required=True)})
            pending_grades={row['chunk_id']:label_grades[row['relevance']]
                for _,row in edited.iterrows() if row['relevance']!='Unjudged'}
            unsaved_grades=pending_grades!=judged
            judged_count=len(pending_grades)
            st.caption(f"Judgment coverage: {judged_count} of {len(chunks)} chunks ({judged_count/max(1,len(chunks)):.0%}). Mark non-relevant passages as grade 0; leave a passage Unjudged only when you have not assessed it."+(" · Save pending changes before running an experiment." if unsaved_grades else ''))
            if st.button('Save relevance grades',key=f"save-judgments-{selected['query_id']}"):
                db.replace_judgments(selected['query_id'],pending_grades)
                st.success(f'Saved {len(pending_grades)} explicit grades.');st.rerun()
    st.divider()
    experiment_name=st.text_input('Experiment name',value='BM25 vs semantic retrieval')
    if st.button('Run paired experiment for all judged queries',type='primary',disabled=not bool(queries)):
        labeled_queries=[(query,db.judgments(query['query_id'])) for query in queries]
        labeled_queries=[(query,grades) for query,grades in labeled_queries if grades]
        if unsaved_grades:
            st.warning('Save the current relevance grades before running the experiment.')
        elif not labeled_queries:
            st.warning('Save relevance grades for at least one query first.')
        elif not chunks:
            st.warning('Index documents before evaluating queries.')
        else:
            configuration={'top_k':config.DEFAULT_TOP_K,'chunk_size_words':config.CHUNK_SIZE,
                'chunk_overlap_words':config.CHUNK_OVERLAP,'latency_runs':config.LATENCY_RUNS,
                'distance_metric':'cosine','model_name':config.MODEL_NAME,
                'latency_scope':{'retrieval_only':'BM25 scoring or Chroma query; excludes index/model setup and query embedding',
                    'end_to_end':'BM25 in-memory index build plus scoring, or query embedding plus Chroma query; model loading and shared SQLite chunk loading excluded'},
                'corpus_chunks':len(chunks)}
            experiment_id=db.create_experiment(experiment_name.strip() or 'BM25 vs semantic retrieval',config.MODEL_NAME,configuration)
            progress=st.progress(0);total=len(labeled_queries)*2;completed=0
            for test_query,grades in labeled_queries:
                coverage=min(1.0,len(grades)/max(1,len(chunks)))
                for method in ('Keyword','Semantic'):
                    found,timing=run_search(db,emb,store,test_query['query_text'],method,config.DEFAULT_TOP_K,config.LATENCY_RUNS,record_history=False)
                    values=metrics([item['chunk_id'] for item in found],grades,config.DEFAULT_TOP_K)
                    values.update(timing);values.update({'judgment_coverage':coverage,
                        'judged_chunks':len(grades),'corpus_chunks':len(chunks)})
                    db.save_evaluation(experiment_id,test_query['query_id'],method,values)
                    completed+=1;progress.progress(completed/total)
            st.success(f"Saved experiment #{experiment_id} with {len(labeled_queries)} judged queries.");st.rerun()
    experiments=db.experiments()
    if experiments:
        experiment=st.selectbox('Review experiment',experiments,
            format_func=lambda x:f"#{x['experiment_id']} · {x['experiment_name']} · {x['timestamp']}")
        rows=db.evaluation_rows(experiment['experiment_id'])
    else:rows=[]
    if rows:
        configuration=json.loads(experiment['configuration'])
        categorized_rows=[{**row,'query_category':row.get('category') or 'Uncategorized'} for row in rows]
        categories=sorted({row['query_category'] for row in categorized_rows})
        selected_category=st.selectbox('Query group',['All groups',*categories])
        display_rows=categorized_rows if selected_category=='All groups' else [row for row in categorized_rows if row['query_category']==selected_category]
        st.caption(f"{len({row['query'] for row in display_rows})} queries · top K {configuration.get('top_k')} · {configuration.get('latency_runs')} timing runs · model {experiment['model_name']}")
        df=pd.DataFrame(display_rows);st.dataframe(df,use_container_width=True,hide_index=True)
        means=df.groupby('method',as_index=False).mean(numeric_only=True)
        metric=st.selectbox('Quality metric',['precision_at_k','recall_at_k','mrr','ndcg_at_k'],format_func=lambda x:{'precision_at_k':'Precision@K','recall_at_k':'Recall@K','mrr':'MRR','ndcg_at_k':'NDCG@K'}[x])
        quality,ret=st.columns(2)
        with quality:st.plotly_chart(px.bar(means,x='method',y=metric,title=metric.replace('_',' ').upper(),range_y=[0,1]),use_container_width=True)
        with ret:st.plotly_chart(px.bar(means,x='method',y='latency_ms',error_y='latency_std_ms',title='Retrieval only · mean ± SD (ms)'),use_container_width=True)
        st.plotly_chart(px.bar(means,x='method',y='end_to_end_ms',error_y='end_to_end_std_ms',title='End to end · mean ± SD (ms)'),use_container_width=True)
        coverage=df.groupby('query',as_index=False)['judgment_coverage'].first()
        if not coverage.empty and coverage['judgment_coverage'].min()<1:
            st.warning('Some query judgments do not cover every corpus chunk. Recall and ranking metrics may be biased; review judgment coverage before reporting results.')
        st.write(summarize(display_rows));st.download_button('Export selected query group CSV',df.to_csv(index=False),f"experiment_{experiment['experiment_id']}.csv",'text/csv')
    else:st.info('Create a query, label relevant chunks, and run paired evaluation to populate this dashboard.')
elif page=='Search History':
    st.markdown('## Search history');rows=db.history()
    if rows:
        df=pd.DataFrame(rows).rename(columns={'timestamp':'Time','query_text':'Query','search_method':'Method','result_count':'Results'})
        df['Measured time (ms)']=df['end_to_end_ms'].fillna(df['latency_ms'])
        df['Timing scope']=df.apply(lambda row:'End to end' if pd.notna(row['end_to_end_ms']) else ('Legacy retrieval only' if row['search_method']=='Semantic' else 'Legacy BM25 index + scoring'),axis=1)
        st.dataframe(df[['Time','Query','Method','Measured time (ms)','Timing scope','Results']],use_container_width=True,hide_index=True)
        pick=st.selectbox('Revisit a search',rows,format_func=lambda x:f"{x['search_method']} · {x['query_text']}")
        with st.expander('Saved results'):st.json(json.loads(pick['results_json']))
        st.download_button('Export history CSV',df.drop(columns=['results_json']).to_csv(index=False),'search_history.csv','text/csv')
    else:st.caption('Search history will appear after your first query.')
elif page=='Settings':
    st.markdown('## Settings');st.json({'embedding_model':config.MODEL_NAME,'embedding_dimensions':384 if config.MODEL_NAME=='all-MiniLM-L6-v2' else ('loaded' if emb.is_loaded else 'loads on first semantic search'),'device':str(getattr(emb.model,'device','auto')) if emb.is_loaded else (config.DEVICE or 'auto selected at inference'),'chunk_size_words':config.CHUNK_SIZE,'chunk_overlap_words':config.CHUNK_OVERLAP,'default_top_k':config.DEFAULT_TOP_K,'latency_runs':config.LATENCY_RUNS,'distance_metric':'cosine','chroma_path':str(config.CHROMA_DIR),'sqlite_path':str(config.DB_PATH)})
    st.caption('Configure SEMSEARCH_MODEL, SEMSEARCH_CHUNK_SIZE, SEMSEARCH_CHUNK_OVERLAP, SEMSEARCH_TOP_K, SEMSEARCH_LATENCY_RUNS or SEMSEARCH_DEVICE, then restart. Re-index after changing model or chunk settings.')
