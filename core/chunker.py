"""Sentence-aware word-window chunking (size/overlap are word counts)."""
import re
import uuid

def normalize(text):
    return re.sub(r'\s+',' ', text.replace('\x00',' ')).strip()

def chunk_pages(pages, document_id, document_name, upload_timestamp, size=500, overlap=75):
    if size < 1 or overlap < 0 or overlap >= size: raise ValueError('Require size > overlap >= 0')
    out=[]; idx=0
    for page in pages:
        text=normalize(page.get('text',''))
        if not text: continue
        sentences=re.split(r'(?<=[.!?])\s+',text)
        bucket=[]; count=0
        def emit(words):
            nonlocal idx
            body=' '.join(words).strip()
            if body:
                out.append({'chunk_id':f'{document_id}:{idx}:{uuid.uuid5(uuid.NAMESPACE_URL, body).hex[:8]}',
                  'document_id':document_id,'document_name':document_name,'page_number':page.get('page_number'),
                  'chunk_index':idx,'source_file':document_name,'upload_timestamp':upload_timestamp,'text':body})
                idx+=1
        for sentence in sentences:
            words=sentence.split()
            if not words: continue
            while len(words)>size:
                part=words[:size]; words=words[size-overlap:];
                if bucket: emit(bucket); bucket=[]; count=0
                emit(part)
            if count+len(words)>size and bucket:
                prior=bucket; emit(prior); bucket=prior[-overlap:] if overlap else []; count=len(bucket)
            bucket.extend(words); count+=len(words)
        if bucket: emit(bucket)
    return out
