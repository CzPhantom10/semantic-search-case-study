"""SQLite persistence for documents, searches, experiments and judgments."""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


def utcnow():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Database:
    def __init__(self, path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def initialize(self):
        with self.connect() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS documents(
              document_id TEXT PRIMARY KEY, filename TEXT NOT NULL, file_type TEXT NOT NULL,
              upload_timestamp TEXT NOT NULL, processing_status TEXT NOT NULL,
              total_pages INTEGER DEFAULT 0, total_chunks INTEGER DEFAULT 0,
              file_hash TEXT UNIQUE, error TEXT);
            CREATE TABLE IF NOT EXISTS chunks(
              chunk_id TEXT PRIMARY KEY, document_id TEXT NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
              chunk_index INTEGER NOT NULL, page_number INTEGER, text TEXT NOT NULL,
              UNIQUE(document_id, chunk_index));
            CREATE TABLE IF NOT EXISTS search_history(
              search_id INTEGER PRIMARY KEY AUTOINCREMENT, query_text TEXT NOT NULL,
              search_method TEXT NOT NULL, timestamp TEXT NOT NULL, latency_ms REAL NOT NULL,
              result_count INTEGER NOT NULL, results_json TEXT NOT NULL DEFAULT '[]',
              retrieval_ms REAL, end_to_end_ms REAL);
            CREATE TABLE IF NOT EXISTS test_queries(
              query_id INTEGER PRIMARY KEY AUTOINCREMENT, query_text TEXT NOT NULL,
              category TEXT DEFAULT '', expected_information TEXT DEFAULT '');
            CREATE TABLE IF NOT EXISTS relevance_judgments(
              query_id INTEGER NOT NULL REFERENCES test_queries(query_id) ON DELETE CASCADE,
              chunk_id TEXT NOT NULL REFERENCES chunks(chunk_id) ON DELETE CASCADE,
              relevance_grade INTEGER NOT NULL CHECK(relevance_grade BETWEEN 0 AND 3),
              PRIMARY KEY(query_id, chunk_id));
            CREATE TABLE IF NOT EXISTS experiments(
              experiment_id INTEGER PRIMARY KEY AUTOINCREMENT, experiment_name TEXT NOT NULL,
              timestamp TEXT NOT NULL, model_name TEXT NOT NULL, configuration TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS evaluation_results(
              evaluation_id INTEGER PRIMARY KEY AUTOINCREMENT,
              experiment_id INTEGER NOT NULL REFERENCES experiments(experiment_id) ON DELETE CASCADE,
              query_id INTEGER NOT NULL REFERENCES test_queries(query_id) ON DELETE CASCADE,
              search_method TEXT NOT NULL, precision_at_k REAL, recall_at_k REAL,
              reciprocal_rank REAL, ndcg_at_k REAL, latency_ms REAL, latency_std_ms REAL,
              end_to_end_ms REAL, end_to_end_std_ms REAL,
              judgment_coverage REAL, judged_chunks INTEGER, corpus_chunks INTEGER,
              UNIQUE(experiment_id, query_id, search_method));
            """)
            columns={r['name'] for r in c.execute('PRAGMA table_info(evaluation_results)')}
            migrations={
                'latency_std_ms':'REAL',
                'end_to_end_ms':'REAL',
                'end_to_end_std_ms':'REAL',
                'judgment_coverage':'REAL',
                'judged_chunks':'INTEGER',
                'corpus_chunks':'INTEGER',
            }
            for name, definition in migrations.items():
                if name not in columns:
                    c.execute(f'ALTER TABLE evaluation_results ADD COLUMN {name} {definition}')
            history_columns={r['name'] for r in c.execute('PRAGMA table_info(search_history)')}
            for name in ('retrieval_ms','end_to_end_ms'):
                if name not in history_columns:
                    c.execute(f'ALTER TABLE search_history ADD COLUMN {name} REAL')

    def add_document(self, doc):
        with self.connect() as c:
            c.execute("INSERT INTO documents VALUES(?,?,?,?,?,?,?,?,?)",
                      (doc['document_id'], doc['filename'], doc['file_type'], doc['upload_timestamp'],
                       doc.get('processing_status','processing'), doc.get('total_pages',0),
                       doc.get('total_chunks',0), doc.get('file_hash'), doc.get('error')))

    def set_document_status(self, document_id, status, pages=0, chunks=0, error=None):
        with self.connect() as c:
            c.execute("UPDATE documents SET processing_status=?,total_pages=?,total_chunks=?,error=? WHERE document_id=?",
                      (status, pages, chunks, error, document_id))

    def add_chunks(self, chunks):
        with self.connect() as c:
            c.executemany("INSERT OR REPLACE INTO chunks VALUES(?,?,?,?,?)",
                [(x['chunk_id'],x['document_id'],x['chunk_index'],x.get('page_number'),x['text']) for x in chunks])

    def delete_document(self, document_id):
        with self.connect() as c:
            c.execute("DELETE FROM documents WHERE document_id=?", (document_id,))

    def documents(self):
        with self.connect() as c: return [dict(r) for r in c.execute("SELECT * FROM documents ORDER BY upload_timestamp DESC")]

    def chunks(self):
        with self.connect() as c:
            return [dict(r) for r in c.execute("SELECT c.*,d.filename FROM chunks c JOIN documents d USING(document_id) WHERE d.processing_status='indexed' ORDER BY c.document_id,c.chunk_index")]

    def counts(self):
        with self.connect() as c:
            return {k:c.execute(q).fetchone()[0] for k,q in {'documents':'SELECT COUNT(*) FROM documents WHERE processing_status=\'indexed\'','chunks':'SELECT COUNT(*) FROM chunks','searches':'SELECT COUNT(*) FROM search_history'}.items()}

    def record_search(self, query, method, latency, results, timings=None):
        with self.connect() as c:
            c.execute("""INSERT INTO search_history(
                query_text,search_method,timestamp,latency_ms,result_count,results_json,retrieval_ms,end_to_end_ms)
                VALUES(?,?,?,?,?,?,?,?)""",
                (query,method,utcnow(),latency,len(results),json.dumps(results,ensure_ascii=False),
                 (timings or {}).get('retrieval_ms'),(timings or {}).get('end_to_end_ms')))

    def history(self, limit=200):
        with self.connect() as c: return [dict(r) for r in c.execute("SELECT * FROM search_history ORDER BY search_id DESC LIMIT ?",(limit,))]

    def add_query(self, text, category='', expected=''):
        with self.connect() as c:
            cur=c.execute("INSERT INTO test_queries(query_text,category,expected_information) VALUES(?,?,?)",(text,category,expected))
            return cur.lastrowid

    def queries(self):
        with self.connect() as c: return [dict(r) for r in c.execute("SELECT * FROM test_queries ORDER BY query_id DESC")]

    def judgments(self, query_id):
        with self.connect() as c: return {r['chunk_id']:r['relevance_grade'] for r in c.execute("SELECT chunk_id,relevance_grade FROM relevance_judgments WHERE query_id=?",(query_id,))}

    def save_judgment(self, query_id, chunk_id, grade):
        with self.connect() as c:
            c.execute("INSERT INTO relevance_judgments VALUES(?,?,?) ON CONFLICT(query_id,chunk_id) DO UPDATE SET relevance_grade=excluded.relevance_grade",(query_id,chunk_id,grade))

    def replace_judgments(self, query_id, judgments):
        """Replace one query's explicit 0–3 labels; omitted chunks remain unjudged."""
        with self.connect() as c:
            c.execute('DELETE FROM relevance_judgments WHERE query_id=?',(query_id,))
            c.executemany('INSERT INTO relevance_judgments(query_id,chunk_id,relevance_grade) VALUES(?,?,?)',
                          [(query_id,chunk_id,int(grade)) for chunk_id,grade in judgments.items()])

    def create_experiment(self, name, model_name, configuration):
        with self.connect() as c:
            cur=c.execute("INSERT INTO experiments(experiment_name,timestamp,model_name,configuration) VALUES(?,?,?,?)",
                           (name,utcnow(),model_name,json.dumps(configuration,sort_keys=True)))
            return cur.lastrowid

    def experiments(self):
        with self.connect() as c:
            return [dict(r) for r in c.execute('''SELECT x.* FROM experiments x
                WHERE EXISTS (SELECT 1 FROM evaluation_results e WHERE e.experiment_id=x.experiment_id)
                ORDER BY x.experiment_id DESC''')]

    def save_evaluation(self, experiment_id, query_id, method, values):
        with self.connect() as c:
            c.execute("""INSERT OR REPLACE INTO evaluation_results(
                experiment_id,query_id,search_method,precision_at_k,recall_at_k,
                reciprocal_rank,ndcg_at_k,latency_ms,latency_std_ms,end_to_end_ms,
                end_to_end_std_ms,judgment_coverage,judged_chunks,corpus_chunks)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
              (experiment_id,query_id,method,values['precision_at_k'],values['recall_at_k'],
               values['mrr'],values['ndcg_at_k'],values.get('retrieval_ms',values.get('latency_ms')),
               values.get('retrieval_std_ms',values.get('latency_std_ms')),
               values.get('end_to_end_ms'),values.get('end_to_end_std_ms'),
               values.get('judgment_coverage'),values.get('judged_chunks'),values.get('corpus_chunks')))

    def evaluation_rows(self, experiment_id=None):
        with self.connect() as c:
            query="""SELECT e.experiment_id,x.experiment_name,x.timestamp,x.configuration,
                q.query_text AS query,q.category AS category,e.search_method AS method,e.precision_at_k,e.recall_at_k,
                e.reciprocal_rank AS mrr,e.ndcg_at_k,e.latency_ms,e.latency_std_ms,
                e.end_to_end_ms,e.end_to_end_std_ms,e.judgment_coverage,e.judged_chunks,e.corpus_chunks
                FROM evaluation_results e JOIN experiments x USING(experiment_id)
                JOIN test_queries q USING(query_id)"""
            params=()
            if experiment_id is not None:
                query+=' WHERE e.experiment_id=?';params=(experiment_id,)
            query+=' ORDER BY e.evaluation_id'
            return [dict(r) for r in c.execute(query,params)]
