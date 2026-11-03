"""Persistent Chroma integration uses tiny deterministic vectors; no model download."""
import pytest
from core.vector_store import VectorStore

def test_chroma_insert_query_and_document_delete(tmp_path):
    pytest.importorskip('chromadb')
    store=VectorStore(tmp_path)
    chunks=[{'chunk_id':'doc:0','text':'security protects networks','document_id':'doc','document_name':'n.txt','chunk_index':0,'page_number':1},
            {'chunk_id':'doc2:0','text':'pasta and water','document_id':'doc2','document_name':'m.txt','chunk_index':0,'page_number':None}]
    import numpy as np
    store.upsert(chunks,np.array([[1.,0.],[0.,1.]],dtype='float32'))
    results=store.query(np.array([1.,0.],dtype='float32'),2)
    assert results[0]['chunk_id']=='doc:0' and results[0]['distance']<0.01
    store.delete_document('doc')
    assert [x['chunk_id'] for x in store.query(np.array([1.,0.]),2)]==['doc2:0']
