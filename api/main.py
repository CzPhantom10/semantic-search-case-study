"""FastAPI layer exposing the local retrieval workspace to the React frontend.

This module is transport only. Extraction, chunking, embedding, retrieval,
metrics and persistence stay in `core/`, `services/` and `database/` .
"""
import hashlib
import json
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import config
from core.chunker import chunk_pages
from core.document_processor import extract_document
from core.embedding_engine import EmbeddingEngine
from core.evaluation import metrics, summarize
from core.vector_store import VectorStore
from database.db_manager import Database, utcnow
from services.search_service import run_search

GRADE_LABELS = {0: "Not relevant", 1: "Marginally relevant", 2: "Relevant", 3: "Highly relevant"}


@lru_cache(maxsize=1)
def services():
    """Build the expensive singletons once per process."""
    return (
        Database(config.DB_PATH),
        EmbeddingEngine(config.MODEL_NAME, config.DEVICE),
        VectorStore(config.CHROMA_DIR),
    )


app = FastAPI(title="Semantic Search Studio API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    method: str = "Semantic"
    k: int = Field(default=config.DEFAULT_TOP_K, ge=1, le=50)


class CompareRequest(BaseModel):
    query: str = Field(min_length=1)
    k: int = Field(default=config.DEFAULT_TOP_K, ge=1, le=50)


class QueryRequest(BaseModel):
    query_text: str = Field(min_length=1)
    category: str = ""
    expected_information: str = ""


class JudgmentRequest(BaseModel):
    """Explicit 0-3 grades keyed by chunk id; omitted chunks stay unjudged."""

    grades: dict[str, int] = {}


class ExperimentRequest(BaseModel):
    experiment_name: str = "BM25 vs semantic retrieval"


def _serialize(items):
    return [
        {
            "chunk_id": item["chunk_id"],
            "text": item["text"],
            "score": item.get("score"),
            "distance": item.get("distance"),
            "metadata": item.get("metadata", {}),
        }
        for item in items
    ]


# ---------------------------------------------------------------- overview


@app.get("/api/stats")
def stats():
    """Counts plus the workflow-completion flags that gate the navigation."""
    db, _, _ = services()
    counts = db.counts()
    methods_by_query: dict[str, set[str]] = {}
    for item in db.history(500):
        methods_by_query.setdefault(item["query_text"], set()).add(item["search_method"])
    has_comparison = any(
        {"Compare · Keyword", "Compare · Semantic"}.issubset(methods)
        for methods in methods_by_query.values()
    )
    return {
        **counts,
        "has_search": bool(methods_by_query),
        "has_comparison": has_comparison,
        "has_experiment": bool(db.experiments()),
    }


@app.get("/api/settings")
def settings():
    _, emb, _ = services()
    return {
        "embedding_model": config.MODEL_NAME,
        "embedding_dimensions": 384 if config.MODEL_NAME == "all-MiniLM-L6-v2" else None,
        "model_loaded": emb.is_loaded,
        "device": str(getattr(emb.model, "device", "auto")) if emb.is_loaded else (config.DEVICE or "auto selected at inference"),
        "chunk_size_words": config.CHUNK_SIZE,
        "chunk_overlap_words": config.CHUNK_OVERLAP,
        "default_top_k": config.DEFAULT_TOP_K,
        "latency_runs": config.LATENCY_RUNS,
        "distance_metric": "cosine",
        "max_upload_mb": config.MAX_UPLOAD_MB,
        "chroma_path": str(config.CHROMA_DIR),
        "sqlite_path": str(config.DB_PATH),
    }


# --------------------------------------------------------------- documents


@app.get("/api/documents")
def documents():
    db, _, _ = services()
    return db.documents()


@app.post("/api/documents")
async def upload_documents(files: list[UploadFile] = File(...)):
    """Extract, chunk, embed and index each upload, reporting per-file outcomes."""
    db, emb, store = services()
    results = []
    for upload in files:
        raw = await upload.read()
        name = upload.filename or "upload"
        suffix = Path(name).suffix.lower()
        if suffix not in config.SUPPORTED_TYPES:
            results.append({"filename": name, "status": "error", "detail": f"Unsupported file type {suffix or '(none)'}"})
            continue
        if len(raw) > config.MAX_UPLOAD_MB * 1024 * 1024:
            results.append({"filename": name, "status": "error", "detail": "Exceeds size limit"})
            continue
        digest = hashlib.sha256(raw).hexdigest()
        if any(d.get("file_hash") == digest for d in db.documents()):
            results.append({"filename": name, "status": "skipped", "detail": "Identical file already indexed"})
            continue
        document_id = hashlib.sha256((digest + name).encode()).hexdigest()[:24]
        destination = config.UPLOAD_DIR / f"{document_id}{suffix}"
        destination.write_bytes(raw)
        timestamp = utcnow()
        try:
            pages = extract_document(destination)
            chunks = chunk_pages(pages, document_id, name, timestamp, config.CHUNK_SIZE, config.CHUNK_OVERLAP)
            if not chunks:
                raise ValueError("No text chunks were produced.")
            db.add_document({
                "document_id": document_id,
                "filename": name,
                "file_type": suffix[1:],
                "upload_timestamp": timestamp,
                "processing_status": "processing",
                "file_hash": digest,
            })
            store.upsert(chunks, emb.encode([chunk["text"] for chunk in chunks]))
            db.add_chunks(chunks)
            pages_with_text = sum(bool(page.get("text", "").strip()) for page in pages)
            db.set_document_status(document_id, "indexed", pages_with_text, len(chunks))
            results.append({
                "filename": name,
                "status": "indexed",
                "detail": f"{len(chunks)} chunks",
                "document_id": document_id,
                "chunks": len(chunks),
            })
        except Exception as error:  # noqa: BLE001 - surfaced to the client verbatim
            # Roll back partial state so a failed upload leaves nothing behind.
            if any(d["document_id"] == document_id for d in db.documents()):
                db.delete_document(document_id)
            try:
                store.delete_document(document_id)
            except Exception:
                pass
            destination.unlink(missing_ok=True)
            results.append({"filename": name, "status": "error", "detail": str(error)})
    return {"results": results}


@app.delete("/api/documents/{document_id}")
def delete_document(document_id: str):
    db, _, store = services()
    document = next((d for d in db.documents() if d["document_id"] == document_id), None)
    if document is None:
        raise HTTPException(404, "Document not found")
    store.delete_document(document_id)
    db.delete_document(document_id)
    (config.UPLOAD_DIR / f"{document_id}.{document['file_type']}").unlink(missing_ok=True)
    return {"deleted": document_id}


@app.get("/api/chunks")
def chunks():
    db, _, _ = services()
    return db.chunks()


# ------------------------------------------------------------------ search


@app.post("/api/search")
def search(request: SearchRequest):
    db, emb, store = services()
    if request.method not in ("Semantic", "Keyword"):
        raise HTTPException(400, "method must be 'Semantic' or 'Keyword'")
    if not db.chunks():
        raise HTTPException(409, "Index a document before searching.")
    items, timing = run_search(db, emb, store, request.query, request.method, request.k)
    return {"method": request.method, "results": _serialize(items), "timing": timing}


@app.post("/api/compare")
def compare(request: CompareRequest):
    """Run one query through both rankers over the same indexed chunks."""
    db, emb, store = services()
    if not db.chunks():
        raise HTTPException(409, "Index a document before searching.")
    payload = {}
    for method in ("Keyword", "Semantic"):
        items, timing = run_search(
            db, emb, store, request.query, method, request.k,
            history_method=f"Compare · {method}",
        )
        payload[method.lower()] = {"method": method, "results": _serialize(items), "timing": timing}
    return payload


@app.get("/api/history")
def history(limit: int = 200):
    db, _, _ = services()
    rows = db.history(limit)
    for row in rows:
        row["results"] = json.loads(row.pop("results_json") or "[]")
        row["timing_scope"] = (
            "End to end" if row.get("end_to_end_ms") is not None
            else ("Legacy retrieval only" if row["search_method"] == "Semantic" else "Legacy BM25 index + scoring")
        )
    return rows


# -------------------------------------------------------------- evaluation


@app.get("/api/queries")
def queries():
    db, _, _ = services()
    return db.queries()


@app.post("/api/queries")
def add_query(request: QueryRequest):
    db, _, _ = services()
    query_id = db.add_query(request.query_text, request.category, request.expected_information)
    return {"query_id": query_id}


@app.get("/api/queries/{query_id}/judgments")
def get_judgments(query_id: int):
    """Every corpus chunk paired with its explicit grade, if one exists."""
    db, _, _ = services()
    judged = db.judgments(query_id)
    corpus = db.chunks()
    return {
        "grade_labels": GRADE_LABELS,
        "judged_chunks": len(judged),
        "corpus_chunks": len(corpus),
        "coverage": len(judged) / max(1, len(corpus)),
        "chunks": [
            {
                "chunk_id": chunk["chunk_id"],
                "document": chunk["filename"],
                "page": chunk.get("page_number"),
                "text": chunk["text"],
                "grade": judged.get(chunk["chunk_id"]),
            }
            for chunk in corpus
        ],
    }


@app.put("/api/queries/{query_id}/judgments")
def put_judgments(query_id: int, request: JudgmentRequest):
    db, _, _ = services()
    if any(grade not in GRADE_LABELS for grade in request.grades.values()):
        raise HTTPException(400, "Relevance grades must be between 0 and 3")
    db.replace_judgments(query_id, request.grades)
    return {"saved": len(request.grades)}


@app.get("/api/experiments")
def experiments():
    db, _, _ = services()
    return db.experiments()


@app.post("/api/experiments")
def run_experiment(request: ExperimentRequest):
    """Paired BM25/semantic run across every query that has saved grades."""
    db, emb, store = services()
    corpus = db.chunks()
    if not corpus:
        raise HTTPException(409, "Index documents before evaluating queries.")
    labeled = [(query, db.judgments(query["query_id"])) for query in db.queries()]
    labeled = [(query, grades) for query, grades in labeled if grades]
    if not labeled:
        raise HTTPException(409, "Save relevance grades for at least one query first.")
    configuration = {
        "top_k": config.DEFAULT_TOP_K,
        "chunk_size_words": config.CHUNK_SIZE,
        "chunk_overlap_words": config.CHUNK_OVERLAP,
        "latency_runs": config.LATENCY_RUNS,
        "distance_metric": "cosine",
        "model_name": config.MODEL_NAME,
        "latency_scope": {
            "retrieval_only": "BM25 scoring or Chroma query; excludes index/model setup and query embedding",
            "end_to_end": "BM25 in-memory index build plus scoring, or query embedding plus Chroma query; model loading and shared SQLite chunk loading excluded",
        },
        "corpus_chunks": len(corpus),
    }
    experiment_id = db.create_experiment(
        request.experiment_name.strip() or "BM25 vs semantic retrieval",
        config.MODEL_NAME,
        configuration,
    )
    for test_query, grades in labeled:
        coverage = min(1.0, len(grades) / max(1, len(corpus)))
        for method in ("Keyword", "Semantic"):
            found, timing = run_search(
                db, emb, store, test_query["query_text"], method,
                config.DEFAULT_TOP_K, config.LATENCY_RUNS, record_history=False,
            )
            values = metrics([item["chunk_id"] for item in found], grades, config.DEFAULT_TOP_K)
            values.update(timing)
            values.update({
                "judgment_coverage": coverage,
                "judged_chunks": len(grades),
                "corpus_chunks": len(corpus),
            })
            db.save_evaluation(experiment_id, test_query["query_id"], method, values)
    return {"experiment_id": experiment_id, "queries": len(labeled)}


@app.get("/api/experiments/{experiment_id}/results")
def experiment_results(experiment_id: int):
    db, _, _ = services()
    rows = db.evaluation_rows(experiment_id)
    if not rows:
        raise HTTPException(404, "No evaluation rows for that experiment")
    for row in rows:
        row["query_category"] = row.get("category") or "Uncategorized"
    return {
        "rows": rows,
        "configuration": json.loads(rows[0]["configuration"]),
        "summary": summarize(rows),
    }


@app.get("/api/experiments/{experiment_id}/export.csv")
def export_experiment(experiment_id: int):
    """CSV of one experiment."""
    import csv
    import io

    db, _, _ = services()
    rows = db.evaluation_rows(experiment_id)
    if not rows:
        raise HTTPException(404, "No evaluation rows for that experiment")
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return PlainTextResponse(
        buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="experiment_{experiment_id}.csv"'},
    )


# Serve the production build when it exists, so one process can host everything.
_DIST = config.BASE_DIR / "web" / "dist"
if _DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def spa(full_path: str):
        """Hand every non-API path to the client router."""
        candidate = _DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_DIST / "index.html")
