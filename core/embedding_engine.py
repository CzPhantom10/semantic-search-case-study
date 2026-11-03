"""Lazy local Sentence Transformers wrapper."""
import numpy as np
class EmbeddingEngine:
    def __init__(self, model_name='all-MiniLM-L6-v2', device=''):
        self.model_name=model_name; self.device=device or None; self._model=None
    @property
    def is_loaded(self): return self._model is not None
    @property
    def model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model=SentenceTransformer(self.model_name, **({'device':self.device} if self.device else {}))
        return self._model
    @property
    def dimension(self): return int(self.model.get_sentence_embedding_dimension())
    def encode(self, texts, batch_size=32):
        if not texts: return np.empty((0,self.dimension),dtype='float32')
        return self.model.encode(texts,batch_size=batch_size,convert_to_numpy=True,normalize_embeddings=True,show_progress_bar=False)
