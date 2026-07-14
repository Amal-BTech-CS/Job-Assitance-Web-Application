from accounts.ai.chatbot.core.config import (
    JOB_INDEX_PATH,
    TOP_K,
)

from accounts.ai.chatbot.llm.groq_client import get_llm
from accounts.ai.chatbot.rag.embeddings import get_embeddings
from accounts.ai.chatbot.rag.retriever import load_retriever


# ==================================
# LLM
# ==================================

llm = get_llm()


# ==================================
# Embeddings
# ==================================

embeddings = get_embeddings()


# ==================================
# Job Retriever
# ==================================

job_retriever = load_retriever(
    JOB_INDEX_PATH,
    embeddings,
    TOP_K,
)