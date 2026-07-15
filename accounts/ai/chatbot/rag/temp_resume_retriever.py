# from langchain_community.vectorstores import FAISS

# from .document_loader import load_resume_documents
# from .chunker import split_documents
# from .embeddings import get_embeddings


# def get_resume_retriever(user):

#     embeddings = get_embeddings()

#     documents = load_resume_documents(user)

#     if not documents:
#         return None

#     chunks = split_documents(documents)

#     db = FAISS.from_documents(
#         chunks,
#         embeddings
#     )

#     return db.as_retriever(
#         search_kwargs={"k": 8}
#     )


# accounts/ai/chatbot/rag/temp_resume_retriever.py
import hashlib
from langchain_community.vectorstores import FAISS

from .document_loader import load_resume_documents
from .chunker import split_documents
from accounts.ai.chatbot.core.resources import embeddings  # reuse the singleton, don't reload

_RETRIEVER_CACHE = {}  # {user_id: (content_hash, retriever)} — per worker process


def _hash(documents):
    text = "\n".join(d.page_content for d in documents)
    return hashlib.md5(text.encode()).hexdigest()


def get_resume_retriever(user):
    documents = load_resume_documents(user)
    if not documents:
        return None

    content_hash = _hash(documents)
    cached = _RETRIEVER_CACHE.get(user.id)
    if cached and cached[0] == content_hash:
        return cached[1]

    chunks = split_documents(documents)
    db = FAISS.from_documents(chunks, embeddings)
    retriever = db.as_retriever(search_kwargs={"k": 8})

    _RETRIEVER_CACHE[user.id] = (content_hash, retriever)
    return retriever