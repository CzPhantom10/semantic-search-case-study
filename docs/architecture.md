# Architecture

Streamlit is the presentation layer. `core/document_processor.py` extracts page-level PDF text via PyMuPDF, paragraphs/tables from DOCX, and UTF-8 text from TXT. The chunker normalizes whitespace and groups sentence units into word-count windows; oversized sentences are windowed. SQLite stores document/chunk records and experiment judgments. ChromaDB separately stores text, metadata, and normalized embeddings in a persistent cosine-distance collection. Sentence Transformers loads lazily on first inference; the default `all-MiniLM-L6-v2` model produces 384 dimensions. BM25 ranks the same SQLite chunk set used to index the vector collection.

Upload processing writes vectors before marking the SQLite document indexed; failed ingestion attempts remove partial vector records and database records. Document deletion removes its Chroma records and cascades SQLite chunks/judgments. Since SQLite and Chroma are separate stores, they cannot share one atomic transaction; the UI cleanup handles ordinary failures but abrupt process termination can require re-indexing/deleting the document.

The Streamlit pages are sections in one app: overview, upload/library, each search method, paired comparison, evaluation, history, and settings. Evaluation configurations and scores are persisted in SQLite alongside queries and judgments. Runtime files live under `data/`; they are excluded from version control.

## Retrieval timing

Keyword latency includes in-memory BM25 scoring over indexed chunks (including constructing its small in-memory index for that request). Semantic database latency measures Chroma query only. It excludes model initialization and query embedding, and therefore is not an end-to-end latency comparison. Evaluation repeats retrieval the configured number of times (default 3) and reports mean/standard deviation. Indexing and embedding time are not yet persisted as experiment metrics. This scope is shown in the UI to avoid misleading interpretation.
