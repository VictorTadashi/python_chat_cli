import os
from pathlib import Path

from dotenv import load_dotenv

# Raiz do projeto: src/chatcli/config.py -> sobe dois níveis
PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY não encontrada. Confira o arquivo .env na raiz do projeto.")

MODEL = "gemini-3.5-flash-lite"
MODEL_FALLBACK = "gemini-3.1-flash-lite"

MAX_OUTPUT_TOKENS = 2048

DB_PATH = PROJECT_ROOT / "chat.db"