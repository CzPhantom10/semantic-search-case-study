from pathlib import Path
import pytest
from core.document_processor import extract_document

def test_txt_extraction_and_empty(tmp_path):
    p=tmp_path/'sample.txt';p.write_text('Hello world',encoding='utf-8')
    assert extract_document(p)==[{'page_number':None,'text':'Hello world'}]
    p.write_text('  ',encoding='utf-8')
    with pytest.raises(ValueError):extract_document(p)

def test_unsupported_type(tmp_path):
    p=tmp_path/'file.csv';p.write_text('a,b')
    with pytest.raises(ValueError):extract_document(p)

def test_docx_and_pdf_page_extraction(tmp_path):
    docx=pytest.importorskip('docx')
    doc=docx.Document();doc.add_paragraph('DOCX content');dp=tmp_path/'a.docx';doc.save(dp)
    assert 'DOCX content' in extract_document(dp)[0]['text']
    fitz=pytest.importorskip('fitz')
    pdf=fitz.open();page=pdf.new_page();page.insert_text((72,72),'PDF content');pp=tmp_path/'a.pdf';pdf.save(pp);pdf.close()
    assert extract_document(pp)[0]['page_number']==1
    assert 'PDF content' in extract_document(pp)[0]['text']

def test_corrupt_and_scanned_pdf_errors(tmp_path):
    fitz=pytest.importorskip('fitz')
    bad=tmp_path/'bad.pdf';bad.write_bytes(b'not a pdf')
    with pytest.raises(Exception):extract_document(bad)
    blank=fitz.open();blank.new_page();p=tmp_path/'blank.pdf';blank.save(p);blank.close()
    with pytest.raises(ValueError,match='OCR'):extract_document(p)
