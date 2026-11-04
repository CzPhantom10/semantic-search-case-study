"""Reusable presentation components for Semantic Search Studio."""
import html
import re

import pandas as pd
import streamlit as st


def render_navigation(options=None):
    """Render the left workspace drawer, including only currently unlocked workflow pages."""
    options=options or ['Overview','Document Library','Upload Documents','Semantic Search',
        'Keyword Search','Compare Search','Evaluation','Search History','Settings']
    icons={'Overview':'⌂','Document Library':'▤','Upload Documents':'＋',
        'Semantic Search':'◉','Keyword Search':'⌕','Compare Search':'⇄',
        'Evaluation':'▥','Search History':'◷','Settings':'⚙'}
    selected=st.session_state.get('studio_navigation_page','Overview')
    if selected not in options:
        selected='Overview'
        st.session_state['studio_navigation_page']=selected
    return st.radio('Workspace',options,index=options.index(selected),
        format_func=lambda page:f"{icons[page]}  {page}",
        label_visibility='collapsed',key='studio_navigation_page')


def set_workspace_page(page):
    """Navigate from a dashboard call to action before the next Streamlit run."""
    st.session_state['studio_navigation_page']=page


def result_card(item, rank, semantic=False, query=''):
    metadata=item.get('metadata',{})
    page=f" · Page {metadata.get('page_number')}" if metadata.get('page_number') not in (None,'') else ''
    score=f"Cosine distance · {item['distance']:.4f}" if semantic else f"BM25 score · {item['score']:.4f}"
    name=html.escape(str(metadata.get('document_name',metadata.get('filename','Document'))))
    body=html.escape(str(item['text']))
    chunk_id=html.escape(str(item['chunk_id']))
    if not semantic:
        for term in set(query.split()):
            if len(term)>1:
                body=re.sub(re.escape(html.escape(term)),lambda match:f'<mark>{match.group(0)}</mark>',body,flags=re.IGNORECASE)
    st.markdown(f"<div class='result'><div class='result-head'><span class='result-title'>#{rank} · {name}{page}</span><span class='score-pill'>{score}</span></div><p>{body}</p><code>{chunk_id}</code></div>",unsafe_allow_html=True)


def page_header(eyebrow, title, description):
    st.markdown(f"<div class='page-head'><div class='eyebrow'>{html.escape(eyebrow)}</div><h1>{html.escape(title)}</h1><p>{html.escape(description)}</p></div>",unsafe_allow_html=True)


def score_guide():
    with st.expander('How to read the scores'):
        left,right=st.columns(2)
        left.markdown('''**BM25 score · higher ranks first**

BM25 measures how strongly a passage matches the query words. It combines term frequency with inverse document frequency. It is a ranking score, **not a percentage or probability**, and is best interpreted within the same query and collection.''')
        right.markdown('''**Cosine distance · lower ranks first**

Cosine distance compares the query and passage embeddings. With normalized vectors, values near **0** indicate more similar directions; values near **2** indicate less similarity. It is a geometric distance, **not a confidence or probability**.''')


def render_upload_inventory(database):
    documents=[item for item in database.documents() if item.get('processing_status')=='indexed']
    st.markdown("<div class='inventory'><div class='inventory-title'>Your indexed documents</div><div class='inventory-sub'>Your local searchable library. Manage or remove files from Document Library.</div></div>",unsafe_allow_html=True)
    if not documents:
        st.info('Your library is empty. Add a document to create your first searchable collection.')
        return
    table=pd.DataFrame([{'File':item['filename'],'Type':item['file_type'].upper(),'Status':'Ready',
        'Chunks':item['total_chunks'],'Pages':item['total_pages'] or '—','Added':item['upload_timestamp']}
        for item in documents])
    st.dataframe(table,use_container_width=True,hide_index=True)
