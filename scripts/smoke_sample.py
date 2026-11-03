"""Run the bundled sample through real extraction, embeddings, BM25 and Chroma."""
from pathlib import Path
import gc
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import CHUNK_OVERLAP, CHUNK_SIZE, MODEL_NAME
from core.chunker import chunk_pages
from core.document_processor import extract_document
from core.embedding_engine import EmbeddingEngine
from core.keyword_engine import KeywordEngine
from core.vector_store import VectorStore


def main():
    sample = ROOT / "samples" / "network_security.txt"
    pages = extract_document(sample)
    chunks = chunk_pages(pages, "sample-security", sample.name, "smoke-test", CHUNK_SIZE, CHUNK_OVERLAP)
    assert chunks, "Sample document should create at least one chunk"

    keyword = KeywordEngine(chunks).search("network security", 5)
    assert keyword and keyword[0]["chunk_id"] == chunks[0]["chunk_id"]

    model = EmbeddingEngine(MODEL_NAME, "cpu")
    vectors = model.encode([x["text"] for x in chunks])
    query_vector = model.encode(["How can I keep my computer safe from online intruders?"])[0]
    assert vectors.shape[1] == 384, f"Expected 384 dimensions, got {vectors.shape[1]}"
    with TemporaryDirectory(prefix="semantic-search-smoke-") as tmp:
        store = VectorStore(Path(tmp) / "chroma")
        store.upsert(chunks, vectors)
        semantic = store.query(query_vector, 5)
        assert semantic and semantic[0]["chunk_id"] == chunks[0]["chunk_id"]
        store.delete_document("sample-security")
        assert store.collection.count() == 0
        store.client._system.stop()
        del store
        gc.collect()
    print(f"Sample passed: {len(chunks)} chunk(s), BM25 hit, semantic hit, {vectors.shape[1]} dimensions, Chroma deletion verified.")


if __name__ == "__main__":
    main()
