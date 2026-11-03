from database.db_manager import Database

def test_document_chunk_cascade_and_search_history(tmp_path):
    db=Database(tmp_path/'test.sqlite3')
    doc={'document_id':'d','filename':'f.txt','file_type':'txt','upload_timestamp':'now','file_hash':'hash'}
    db.add_document(doc);db.add_chunks([{'chunk_id':'d:0','document_id':'d','chunk_index':0,'page_number':None,'text':'body'}])
    assert db.counts()['chunks']==1
    db.record_search('q','Keyword',1.25,[{'chunk_id':'d:0'}])
    assert db.history()[0]['result_count']==1
    qid=db.add_query('find body')
    experiment=db.create_experiment('test','model',{'top_k':5})
    db.save_evaluation(experiment,qid,'Keyword',{'precision_at_k':1,'recall_at_k':1,'mrr':1,'ndcg_at_k':1,'latency_ms':1.2,'latency_std_ms':0.1})
    assert db.evaluation_rows()[0]['latency_std_ms']==0.1
    db.delete_document('d');assert db.counts()['chunks']==0
