# Project context

## Academic case study title

**Case Study: Traditional Keyword Search vs AI-Powered Semantic Search Using ChromaDB**

## Application identity

The software is presented as **Semantic Search Studio**, a local document search application. The academic report and project documentation explain that the application supports the case study named above. Keep the product interface focused on document search and comparison; keep the case study framing in the documentation and report.

## Purpose

Build a locally runnable document retrieval platform that compares two approaches over the same indexed passages:

- **BM25 keyword retrieval**, useful when query wording matches exact terms, names, identifiers, and technical vocabulary.
- **Vector semantic retrieval**, using local Sentence Transformers embeddings and persistent ChromaDB cosine search, useful for related wording and paraphrases.

The project investigates where each approach works well and where it struggles. It must not assume semantic search is always better.

## Core workflow and scope

1. Upload PDF, DOCX, or TXT files; extract text and preserve PDF page numbers where available.
2. Normalize and chunk text, retaining source metadata.
3. Embed chunks locally with `all-MiniLM-L6-v2` (384 dimensions by default) and persist vectors in ChromaDB.
4. Search the same chunks with BM25 and vector similarity; compare ranked passages, sources, scores, and latency.
5. Define categorized queries (for example, paraphrase, exact match, identifier, and domain terminology) and manually judge relevance.
6. Evaluate with Precision@K, Recall@K, MRR, NDCG@K, and latency, then export actual results for analysis.

## Technology and operating constraints

Python and Streamlit; Sentence Transformers; ChromaDB; SQLite; Plotly; PyMuPDF; python-docx; and a local BM25 implementation. The app should work on Windows and CPU without paid API access. CUDA may be optional. Runtime uploads and databases remain local.

Default chunk settings are 500 whitespace-delimited words with 75 words of overlap. They are word counts, not a tokenizer-specific token guarantee. PDF pages are one-based; DOCX and TXT do not have reliable page metadata.

## Research integrity

- Both methods must use the same corpus, chunk boundaries, query, and top K.
- Distinguish retrieval-only latency from end-to-end query latency. Exclude model loading from online query timing and state what each measurement includes.
- Retain query-level results, run configuration, repeated-run variation, and judgment coverage.
- Do not treat unjudged passages as confirmed irrelevant without disclosing incomplete judgments.
- Never invent relevance labels, experimental values, findings, or citations.
- Explain that embeddings and ChromaDB are not RDF, OWL, or ontology reasoning. The RDFLib example is a separate Semantic Web illustration.
- Report findings only after running the app on a documented corpus with human relevance judgments.

## Current academic deliverables

The repository contains an evaluation workflow, sample text and query prompts, architecture and methodology notes, and a report outline. The final corpus, complete judgments, measured experimental results, verified references, and report content must be supplied or reviewed as part of the student's study. Keep generated report artifacts in the root `report/` folder.

