# Semantic Search Lab

A local Streamlit case study comparing traditional BM25 keyword retrieval with embedding-based semantic retrieval using Sentence Transformers and persistent ChromaDB. Upload your own PDF, DOCX, or TXT corpus, compare rankings side by side, and evaluate both methods against relevance judgments you provide. No paid API key or hosted LLM is required.

## Features

- PDF extraction with one-based page metadata, DOCX paragraph/table extraction, and TXT extraction with UTF-8 replacement for malformed bytes.
- Sentence-aware word-window chunks, local `all-MiniLM-L6-v2` embeddings, persistent ChromaDB cosine search, and a BM25 baseline.
- Comparison and method-specific search, search history, document removal, query creation, manual relevance labels, Precision@K, Recall@K, MRR, NDCG@K, latency, charts, and CSV export.
- SQLite metadata/history/judgment persistence; independent Chroma vector persistence.
- Separate RDFLib triple demonstration (`python utils/rdf_demo.py`) and academic notes distinguishing RDF/OWL reasoning from vector similarity.

The starter text in `samples/` can be used for a first demo. The evaluation interface intentionally produces no quality scores until a person supplies relevance judgments.

After installing dependencies and caching the embedding model, run a full sample pipeline smoke check with `python scripts/smoke_sample.py`. It uses a temporary Chroma directory and deletes it after checking retrieval/deletion.

## Requirements and Windows setup

Use Python 3.10 or 3.11 (64-bit). The app runs on CPU; PyTorch/Sentence Transformers may download model weights on first use. CUDA is optional. Allow several GB for Python packages and model cache.

In PowerShell, from this project directory:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
streamlit run app.py
```

If PowerShell blocks activation, use `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` for that terminal session, or invoke `.\.venv\Scripts\python.exe -m streamlit run app.py` directly. Open the local URL Streamlit prints. On first model use, Sentence Transformers downloads the configured model; thereafter inference is local.

## Tests

```powershell
pytest -q
```

Tests needing PyMuPDF, python-docx, or ChromaDB skip when those packages are unavailable. The Chroma test uses tiny deterministic vectors and requires no model download. Tests were authored with the project but could not be run in the current development shell because Python is not installed/on PATH.

## Configuration

Defaults are in `config.py`; copy `.env.example` to `.env` and edit it to set overrides. Main settings: model name, device, chunk size/overlap (word counts), top K, latency repeat count, upload cap, and data directory. Changing model or chunk settings requires re-indexing existing documents. `all-MiniLM-L6-v2` returns 384-dimensional vectors. Chroma uses cosine distance; lower distance means closer vectors and is not a calibrated probability.

## Data and persistence

`data/uploads/` holds originals, `data/chroma_db/` the persistent vector collection, and `data/semantic_search.sqlite3` SQLite records. These files are local and ignored by Git. Back up both SQLite and Chroma together. Deleting a document removes its vectors and cascades SQLite chunks and judgments. Since SQLite and Chroma cannot participate in one transaction, a sudden process termination during ingestion may need a manual delete/re-index from the Document Library.

## Project layout

```text
app.py                    Streamlit navigation, forms, charts and result views
config.py                 Local paths and environment configuration
core/                     Extraction, chunking, embeddings, BM25, Chroma, metrics
database/db_manager.py    SQLite schema and persistence operations
pages/                    Reserved for future Streamlit page split
assets/                   Reserved for additional styling/static assets
samples/                  Small starter document and query examples
tests/                    Unit tests for processing, retrieval, metrics, persistence
docs/                     Architecture, method, evaluation guide, report outline
utils/rdf_demo.py         Independent RDF triple exercise
data/                     Runtime uploads, vector index, and SQLite database
```

## Academic use and interpretation

RDF/OWL provide explicit symbolic facts, schemas, and possible logical inference; embeddings represent distributional relationships as dense vectors. They answer related but distinct questions. ChromaDB stores vectors and metadata; it is not an RDF graph store or an ontology reasoner. Consult `docs/methodology.md` and `docs/evaluation_guide.md` before reporting results.

Latency is scoped carefully: BM25 currently rebuilds its in-memory index for each request; the semantic measurement covers Chroma retrieval but excludes model load and query embedding. The evaluation repeats retrieval according to `SEMSEARCH_LATENCY_RUNS` (default 3) and reports mean and standard deviation. These values are not a like-for-like end-to-end performance benchmark. Evaluation runs and configuration, judgments, and search history persist in SQLite; tables are exportable. No experimental findings or citations are supplied as facts.

## Troubleshooting

- **Missing Python:** install 64-bit Python 3.10/3.11 and enable the Python Launcher, then rerun the setup commands.
- **Model download or memory issues:** ensure internet access for the initial model download; set `SEMSEARCH_DEVICE=cpu`. Reduce chunk size or batch inference only if you modify the embedding wrapper.
- **Scanned PDF:** image-only PDFs require OCR; this version reports that no text is extractable.
- **Chroma/model mismatch after changing model:** clear/re-index documents using the app and a clean collection/data directory, because dimensions must match the chosen embedding model.
- **PowerShell activation policy:** use the process-scoped command above or run the venv executable directly.

## Known limitations and future work

OCR, optional grounded LLM answers, re-index-in-place, end-to-end latency timing, and a hybrid search mode are not implemented. DOCX and TXT do not provide page numbers. Manual judgments require careful coverage to avoid treating unjudged relevant passages as irrelevant. The initial evaluation UI uses binary labels, while NDCG supports graded labels in the metric module.
