# Academic report outline

## Abstract
Problem, research question, corpus, methods, principal measured findings, and limitations. Fill findings only after running a labeled experiment.

## Chapter 1 — Introduction
Semantic Web and information retrieval context; motivation; problem statement; objectives; scope; research questions.

## Chapter 2 — Background and related concepts
Keyword retrieval and BM25; tokenization and chunking; NLP embeddings; vector similarity; ChromaDB; RDF, OWL, ontology reasoning, and how they differ from distributional embeddings. Add properly verified citations from sources consulted by the student.

## Chapter 3 — Requirements and design
Functional/non-functional requirements; architecture; data flow; SQLite schema; vector metadata; interface and privacy decisions.

## Chapter 4 — Implementation
Extraction, preprocessing, chunking, local model, persistent vector index, BM25 baseline, UI, history, and judgment workflow. Include configuration and runtime versions.

## Chapter 5 — Experimental methodology
Corpus selection and licensing; query categories; relevance protocol; top K; model/chunk parameters; metrics; timing scope; hardware/software; repeated-run protocol.

## Chapter 6 — Results and discussion
Insert exported real tables/plots, per-query breakdown, averages and variability. Explain cases favoring lexical or semantic retrieval. Do not generalize beyond the collection and judgments.

## Chapter 7 — Limitations and ethics
Small/biased corpus, subjective judgments, incomplete labels, chunk boundaries, language/domain coverage, local model and resource constraints, OCR absence, and timing-scope differences.

## Chapter 8 — Conclusion and future work
Answer research questions from observed evidence. Future work can add OCR, persisted experiment runs, repeated latency protocols, hybrid retrieval, RDF/ontology-aware retrieval, and optional grounded generation.

## Appendices
Setup, configuration, test commands/results, sample queries, judgment rubric, exported raw data, and source code.
