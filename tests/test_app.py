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
    db.set_document_status(document_id,'indexed',0,1)
    app=Path(__file__).resolve().parents[1]/'app.py'
    try:
        result=AppTest.from_file(str(app),default_timeout=30).run()
        assert not result.exception
        assert any('Find the meaning behind your documents' in item.value for item in result.markdown)
        result.radio[0].set_value('Upload Documents').run()
        assert not result.exception
        assert any('Your indexed documents' in item.value for item in result.markdown)
        assert any(filename in str(table.value) for table in result.dataframe)
        result.radio[0].set_value('Compare Search').run()
        assert not result.exception
        assert any('How to read the scores' in item.label for item in result.expander)
    finally:
        db.delete_document(document_id)
