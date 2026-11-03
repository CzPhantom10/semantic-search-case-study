from core.chunker import chunk_pages

def test_chunking_preserves_metadata_and_overlap():
    pages=[{'page_number':4,'text':'One short sentence. Two short sentence. Three short sentence.'}]
    chunks=chunk_pages(pages,'doc','sample.txt','now',size=5,overlap=2)
    assert chunks
    assert all(c['document_id']=='doc' and c['page_number']==4 for c in chunks)
    assert [c['chunk_index'] for c in chunks]==list(range(len(chunks)))

def test_empty_pages_skipped_and_bad_config_rejected():
    assert chunk_pages([{'page_number':1,'text':'  '}],'d','f','t')==[]
    try: chunk_pages([], 'd','f','t',size=3,overlap=3)
    except ValueError: pass
    else: raise AssertionError('overlap must be smaller than chunk size')
