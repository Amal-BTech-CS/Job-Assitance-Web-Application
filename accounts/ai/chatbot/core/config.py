from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv()


# ==================================
# Groq
# ==================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

MODEL_NAME = "llama-3.3-70b-versatile"


# ==================================
# RAG
# ==================================

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

TOP_K = 8


# ==================================
# Paths
# ==================================

# accounts/ai/chatbot/
CHATBOT_DIR = Path(__file__).resolve().parents[1]

VECTORSTORE_DIR = CHATBOT_DIR / "vectorstores"

JOB_INDEX_PATH = VECTORSTORE_DIR / "job_index"