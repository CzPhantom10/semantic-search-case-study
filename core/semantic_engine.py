"""Semantic search with measured retrieval latency excluding model load/encoding."""
import time
class SemanticEngine:
    def __init__(self, embeddings, store): self.embeddings=embeddings; self.store=store
    def search(self, query, k=5):
        vector=self.embeddings.encode([query])[0]  # query inference is reported separately from DB retrieval
        start=time.perf_counter(); results=self.store.query(vector,k); latency=(time.perf_counter()-start)*1000
        return results,latency
