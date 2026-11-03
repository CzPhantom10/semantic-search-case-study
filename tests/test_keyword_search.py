from core.keyword_engine import KeywordEngine

def test_bm25_ranks_relevant_chunk_and_returns_scores():
    chunks=[{'chunk_id':'a','text':'Network security helps prevent cyberattacks.'},
            {'chunk_id':'b','text':'Cooking pasta requires salted boiling water.'}]
    result=KeywordEngine(chunks).search('network security',5)
    assert result[0]['chunk_id']=='a' and result[0]['score']>0
    assert len(result)==1

def test_empty_query():
    assert KeywordEngine([{'chunk_id':'a','text':'Some text'}]).search('!!!')==[]
