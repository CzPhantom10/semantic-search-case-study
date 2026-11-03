import math
from core.evaluation import metrics

def test_metrics_binary_and_graded():
    m=metrics(['bad','good'],{'good':2,'bad':0,'also-good':1},2)
    assert m['precision_at_k']==.5
    assert m['recall_at_k']==.5
    assert m['mrr']==.5
    assert 0 < m['ndcg_at_k'] < 1

def test_no_judgments_has_undefined_recall_and_ndcg():
    m=metrics(['a'],{},1)
    assert m['recall_at_k'] is None and m['ndcg_at_k'] is None
