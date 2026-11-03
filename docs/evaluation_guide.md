# Evaluation guide

1. Upload a representative collection of PDF, DOCX, or TXT files and wait for each to be indexed.
2. Open Evaluation and create queries spanning paraphrases, exact names/identifiers, and domain terminology.
3. For each query, inspect the corpus and mark all relevant chunks. A judgment is tied to a chunk ID; changing the corpus/chunking requires rechecking judgments.
4. Run the paired evaluation. Both methods use the same query and top K. Unjudged items count as non-relevant, so incomplete judgments bias scores downward.
5. Review query-level values alongside averages. Compare Precision@K, Recall@K, MRR, and NDCG@K; recall is undefined when no relevant items are labeled. Latency runs repeat according to `SEMSEARCH_LATENCY_RUNS` (default 3); the chart reports the mean and standard deviation.
6. Evaluation runs, parameters, timestamps, and per-method scores persist in SQLite. Export the evaluation table to CSV when preparing analysis outside the application.

Latency caveat: BM25 timing includes construction of its in-memory term index for the request. Semantic timing covers Chroma query and excludes query embedding/model initialization. Neither includes upload/indexing. Experiment configuration and scores persist, while repeated-run mean and standard deviation are recorded per query/method. Disclose the exact timing scope when reporting an experiment.
