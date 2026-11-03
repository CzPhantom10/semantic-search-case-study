# Methodology

## Research question

For a fixed document collection, query set, and chunking configuration, how do BM25 lexical retrieval and embedding-based cosine retrieval differ in relevance quality and measured retrieval time?

## Corpus and preprocessing

Use the same uploaded source files and chunk boundaries for both methods. PDF page numbers are one-based; DOCX/TXT have no reliable page model and are displayed without page values. The default chunk window is 500 whitespace-delimited words with 75 words of overlap; it is sentence-aware except when a sentence exceeds the window. This is a transparent, reproducible word-count heuristic, not a tokenizer-specific 500-token guarantee. Record any changes to chunk size/overlap and re-index before an experiment.

## Methods

BM25 uses lowercase Unicode word tokens, `k1=1.5`, `b=0.75`, and standard positive IDF. Semantic retrieval uses local Sentence Transformers `all-MiniLM-L6-v2`, normalized vectors, and ChromaDB cosine distance. Smaller cosine distance indicates closer vectors; it is neither a probability nor a relevance percentage. Both retrieve from the same corpus and use the same top K.

## Judgments and metrics

Create natural-language test queries and label relevant chunks in the Evaluation page. Current UI judgments are binary in practice (relevant=2, non-relevant=0), while the metric implementation supports grades 0–3 for NDCG. Unjudged chunks are treated as grade 0; consequently, judge the corpus sufficiently before interpreting metrics. Precision@K divides hits by configured K, including when fewer than K results exist. Recall is undefined when there are no known relevant chunks and is omitted from averages. MRR uses the first relevant retrieved item. NDCG uses gain `2^grade-1` and logarithmic rank discount.

Latency values are observed, not predicted. Keyword latency includes query scoring plus per-request in-memory index construction. Chroma latency excludes embedding generation and model loading. Do not claim an end-to-end speed advantage from these differently scoped measurements; for that comparison, time embedding and retrieval together in a separate protocol. Repeat runs and report variability for formal conclusions.

## Academic context

RDF represents facts as subject–predicate–object triples and OWL can define ontology classes, properties, and logical constraints. These are explicit, machine-readable symbolic representations that support graph querying and, with an appropriate reasoner, ontology reasoning. Distributional embeddings instead map text to dense numeric vectors learned from language usage; proximity captures statistical semantic association. Embeddings are not RDF triples, do not inherently expose named relations, and cosine similarity is not ontology inference. ChromaDB is a vector database, not an RDF store. The separate `utils/rdf_demo.py` demonstrates a triple without joining it to the retrieval pipeline.
