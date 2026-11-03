"""Semantic search with retrieval-only and end-to-end query timings."""
import time
class SemanticEngine:
    def __init__(self, embeddings, store): self.embeddings=embeddings; self.store=store
    def search(self, query, k=5):
        # Load weights before timing so the online measurement excludes one-time startup.
        _ = self.embeddings.model
        end_to_end_start=time.perf_counter()
        vector=self.embeddings.encode([query])[0]
        retrieval_start=time.perf_counter()
        results=self.store.query(vector,k)
        end_to_end_ms=(time.perf_counter()-end_to_end_start)*1000
        retrieval_ms=(time.perf_counter()-retrieval_start)*1000
        return results,{'retrieval_ms':retrieval_ms,'end_to_end_ms':end_to_end_ms}
