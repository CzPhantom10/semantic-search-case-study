"""Application configuration, overridable through environment variables."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / '.env')
except ImportError:
    pass
DATA_DIR = Path(os.getenv("SEMSEARCH_DATA_DIR", BASE_DIR / "data"))
UPLOAD_DIR = DATA_DIR / "uploads"
CHROMA_DIR = DATA_DIR / "chroma_db"
DB_PATH = DATA_DIR / "semantic_search.sqlite3"
MODEL_NAME = os.getenv("SEMSEARCH_MODEL", "all-MiniLM-L6-v2")
CHUNK_SIZE = int(os.getenv("SEMSEARCH_CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("SEMSEARCH_CHUNK_OVERLAP", "75"))
DEFAULT_TOP_K = int(os.getenv("SEMSEARCH_TOP_K", "5"))
LATENCY_RUNS = max(1, int(os.getenv("SEMSEARCH_LATENCY_RUNS", "3")))
DEVICE = os.getenv("SEMSEARCH_DEVICE", "")  # blank lets Sentence Transformers select CPU/CUDA
MAX_UPLOAD_MB = int(os.getenv("SEMSEARCH_MAX_UPLOAD_MB", "50"))
SUPPORTED_TYPES = {".pdf", ".docx", ".txt"}
for _path in (DATA_DIR, UPLOAD_DIR, CHROMA_DIR):
    _path.mkdir(parents=True, exist_ok=True)
