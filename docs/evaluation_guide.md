# Evaluation guide

1. Upload a representative collection of PDF, DOCX, or TXT files and wait for each to be indexed.
2. Open Evaluation and create queries spanning paraphrases, exact names/identifiers, and domain terminology. Record a useful category (for example, `paraphrase`, `exact`, or `identifier`) so you can inspect those groups separately.
3. For each query, inspect the corpus and grade each chunk from 0 (not relevant) to 3 (highly relevant). Leave a chunk Unjudged only if you have not assessed it. Judgments attach to chunk IDs; changing the corpus/chunking requires rechecking them.
4. Save grades, then run a paired experiment across all queries with saved judgments. Both methods use the same query and top K. The app records judgment coverage; incomplete judgments can bias metrics because unjudged passages are treated as grade 0.
5. Select one experiment in the results view. Compare query-level values and averages for Precision@K, Recall@K, MRR, and NDCG@K. Recall is undefined when there are no known relevant items.
6. Review both latency scopes. Retrieval-only measures BM25 scoring or the Chroma query. End-to-end query timing includes BM25 index construction or semantic query embedding plus vector retrieval. Model loading and shared SQLite chunk loading are excluded. Each scope repeats according to `SEMSEARCH_LATENCY_RUNS` (default 3), and the chart reports mean and standard deviation.
7. Experiment configuration, timestamps, scores, judgment coverage, and per-method results persist in SQLite. Export the selected experiment to CSV for analysis and reporting.

Latency caveat: neither scope includes document upload/indexing, model loading, or shared SQLite chunk loading. State the timing scope when reporting an experiment, and do not treat retrieval-only latency as end-to-end response time.
