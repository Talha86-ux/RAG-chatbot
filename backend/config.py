import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_store")
DATA_DIR = os.getenv("DATA_DIR", "./data")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")

if not OPENAI_API_KEY:
    raise ValueError(
        "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
    )