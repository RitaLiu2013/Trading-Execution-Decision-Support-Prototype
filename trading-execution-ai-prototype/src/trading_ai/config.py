from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PACKAGE_ROOT / "data"
KNOWLEDGE_DIR = PACKAGE_ROOT / "knowledge"
OUTPUT_DIR = PACKAGE_ROOT / "outputs"

RAW_DATA_PATH = DATA_DIR / "synthetic_trades.csv"
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
OLLAMA_MODEL_NAME = "qwen3:4b-instruct"
REFUSAL_TEXT = "The retrieved context is insufficient."
