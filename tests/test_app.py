from pathlib import Path
from uuid import uuid4
import pytest

def test_overview_page_renders_without_streamlit_exception():
    streamlit=pytest.importorskip('streamlit')
    pytest.importorskip('plotly')
    AppTest=pytest.importorskip('streamlit.testing.v1').AppTest
    from config import DB_PATH
    from database.db_manager import Database, utcnow
    db=Database(DB_PATH)
    document_id=f"ui-probe-{uuid4().hex}"
    filename='ui-inventory-probe.txt'
    db.add_document({'document_id':document_id,'filename':filename,'file_type':'txt','upload_timestamp':utcnow(),'processing_status':'processing','file_hash':uuid4().hex})
    search_query=f"network security {document_id}"
    db.add_chunks([{'chunk_id':f'{document_id}:0','document_id':document_id,'chunk_index':0,
        'page_number':None,'text':f'This sample explains network security for {document_id}.'}])
    db.set_document_status(document_id,'indexed',0,1)
    app=Path(__file__).resolve().parents[1]/'app.py'
    try:
        result=AppTest.from_file(str(app),default_timeout=30).run()
        assert not result.exception
        assert any('Search your documents.' in item.value for item in result.markdown)
        result.radio[0].set_value('Upload Documents').run()
        assert not result.exception
        assert any('Your indexed documents' in item.value for item in result.markdown)
        assert any(filename in str(table.value) for table in result.dataframe)
        result.radio[0].set_value('Keyword Search').run()
        result.text_input[0].set_value(search_query).run()
        result.button[0].click().run()
        assert not result.exception
        next_compare=next(button for button in result.button if button.label=='Next: compare both methods')
        next_compare.click().run()
        assert not result.exception
        assert any('Compare methods' in item.value for item in result.markdown)
        assert any('How to read the scores' in item.label for item in result.expander)
    finally:
        db.delete_document(document_id)
        with db.connect() as connection:
            connection.execute('DELETE FROM search_history WHERE query_text=?',(search_query,))
