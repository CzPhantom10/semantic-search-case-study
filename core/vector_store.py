"""Persistent ChromaDB wrapper; cosine distance is returned as raw distance."""
class VectorStore:
    def __init__(self, path, collection='document_chunks'):
        import chromadb
        self.client=chromadb.PersistentClient(path=str(path))
        self.collection=self.client.get_or_create_collection(collection,metadata={'hnsw:space':'cosine'})
    def upsert(self, chunks, embeddings):
        if not chunks:return
        self.collection.upsert(ids=[x['chunk_id'] for x in chunks],documents=[x['text'] for x in chunks],
          embeddings=embeddings.tolist(),metadatas=[{k:(v if v is not None else '') for k,v in x.items() if k not in ('text',)} for x in chunks])
    def delete_document(self, document_id): self.collection.delete(where={'document_id':document_id})
    def query(self, embedding, k=5):
        if not self.collection.count(): return []
        res=self.collection.query(query_embeddings=[embedding.tolist()],n_results=min(k,self.collection.count()),include=['documents','metadatas','distances'])
        return [{'chunk_id':i,'text':t,'distance':float(d),'metadata':m} for i,t,d,m in zip(res['ids'][0],res['documents'][0],res['distances'][0],res['metadatas'][0])]
