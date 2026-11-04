"""Retrieval service with repeatable retrieval-only and end-to-end timings."""
import statistics
import time

from core.keyword_engine import KeywordEngine
from core.semantic_engine import SemanticEngine


def run_search(database, embeddings, vector_store, query, method, k, repeats=1, record_history=True, history_method=None):
    chunks=database.chunks() if method=='Keyword' else None
    if method=='Semantic':
        _=embeddings.model  # one-time model loading is outside online query timing
    retrieval_runs=[]
    end_to_end_runs=[]
    items=[]
    for _ in range(max(1,repeats)):
        end_start=time.perf_counter()
        if method=='Keyword':
            engine=KeywordEngine(chunks)
            retrieval_start=time.perf_counter()
            items=engine.search(query,k)
            retrieval_runs.append((time.perf_counter()-retrieval_start)*1000)
        elif method=='Semantic':
            items,measurement=SemanticEngine(embeddings,vector_store).search(query,k)
            retrieval_runs.append(measurement['retrieval_ms'])
        else:
            raise ValueError(f'Unknown retrieval method: {method}')
        end_to_end_runs.append((time.perf_counter()-end_start)*1000)
    for item in items:
        item['metadata'].setdefault('filename',item['metadata'].get('document_name',''))
    timing={'retrieval_ms':statistics.mean(retrieval_runs),
        'retrieval_std_ms':statistics.pstdev(retrieval_runs),
        'end_to_end_ms':statistics.mean(end_to_end_runs),
        'end_to_end_std_ms':statistics.pstdev(end_to_end_runs)}
    packed=[{'chunk_id':item['chunk_id'],'text':item['text'],'score':item.get('score'),
        'distance':item.get('distance'),'metadata':item.get('metadata',{})} for item in items]
    if record_history:
        database.record_search(query,history_method or method,timing['end_to_end_ms'],packed,timing)
    return items,timing
