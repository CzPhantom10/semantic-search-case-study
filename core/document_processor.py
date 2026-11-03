"""File extraction with page-aware PDF metadata."""
from pathlib import Path


def extract_document(path):
    path=Path(path); suffix=path.suffix.lower()
    if suffix=='.pdf':
        import fitz
        pages=[]
        with fitz.open(path) as pdf:
            for i,page in enumerate(pdf,1): pages.append({'page_number':i,'text':page.get_text('text') or ''})
        if not any(p['text'].strip() for p in pages):
            raise ValueError('This PDF contains no extractable text. Scanned PDFs need OCR, which is not included.')
        return pages
    if suffix=='.docx':
        from docx import Document
        doc=Document(path); text='\n'.join(p.text for p in doc.paragraphs if p.text.strip())
        text += '\n'+'\n'.join(' | '.join(cell.text for cell in row.cells) for table in doc.tables for row in table.rows)
        if not text.strip(): raise ValueError('The document contains no extractable text.')
        return [{'page_number':None,'text':text}]
    if suffix=='.txt':
        raw=path.read_bytes()
        text=raw.decode('utf-8-sig',errors='replace')
        if not text.strip(): raise ValueError('The document is empty.')
        return [{'page_number':None,'text':text}]
    raise ValueError(f'Unsupported file type: {suffix}')
