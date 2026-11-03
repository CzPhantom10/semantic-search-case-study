"""IR metrics and fair paired evaluation helpers."""
import math
def metrics(retrieved_ids, grades, k=5):
    ranked=list(retrieved_ids[:k]); relevant={cid for cid,g in grades.items() if g>0}
    hits=sum(cid in relevant for cid in ranked)
    precision=hits/k if k else 0.0
    recall=hits/len(relevant) if relevant else None
    rr=next((1/(i+1) for i,cid in enumerate(ranked) if cid in relevant),0.0)
    def dcg(vals): return sum((2**g-1)/math.log2(i+2) for i,g in enumerate(vals))
    actual=dcg([grades.get(cid,0) for cid in ranked]); ideal=dcg(sorted(grades.values(),reverse=True)[:k])
    return {'precision_at_k':precision,'recall_at_k':recall,'mrr':rr,'ndcg_at_k':actual/ideal if ideal else None}

def summarize(rows):
    if not rows:return 'No evaluated queries with saved relevance judgments yet.'
    methods={}
    for method in sorted({r['method'] for r in rows}):
        group=[r for r in rows if r['method']==method]
        methods[method]={key:sum(r[key] for r in group if r.get(key) is not None)/max(1,sum(r.get(key) is not None for r in group)) for key in ('precision_at_k','recall_at_k','mrr','ndcg_at_k','latency_ms')}
    if len(methods)<2:return f"Evaluation recorded for {next(iter(methods))}; add comparable results to compare methods."
    a,b=list(methods.items()); winner=max((a,b),key=lambda x:x[1]['ndcg_at_k'] or 0)
    return f"Across {len({r['query'] for r in rows})} evaluated queries, {winner[0]} has the higher mean NDCG@K ({winner[1]['ndcg_at_k']:.3f}). Results vary by query; inspect per-query scores and latency before drawing conclusions."
