from langchain_community.vectorstores import FAISS

from .document_loader import load_resume_documents
from .chunker import split_documents
from .embeddings import get_embeddings


def get_resume_retriever(user):

    embeddings = get_embeddings()

    documents = load_resume_documents(user)

    if not documents:
        return None

    chunks = split_documents(documents)

    db = FAISS.from_documents(
        chunks,
        embeddings
    )

    return db.as_retriever(
        search_kwargs={"k": 8}
    )