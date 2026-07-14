from pathlib import Path

from .rag.document_loader import (
    load_job_documents,
    load_resume_documents,
)

from .rag.chunker import split_documents
from .rag.embeddings import get_embeddings
from .rag.index_builder import build_and_save


embeddings = get_embeddings()

# accounts/ai/chatbot/
BASE_DIR = Path(__file__).resolve().parent

VECTORSTORE_DIR = BASE_DIR / "vectorstores"


def build_job_index():
    """
    Build FAISS index for all jobs in the database.
    """

    documents = load_job_documents()

    if not documents:
        print("No jobs found.")
        return

    chunks = split_documents(documents)

    save_path = VECTORSTORE_DIR / "job_index"

    build_and_save(
        chunks,
        embeddings,
        save_path
    )

    print("Job index rebuilt successfully.")


def build_resume_index(user):
    """
    Optional:
    Creates a permanent resume index for a user.
    (Currently not used because we're using a temporary FAISS retriever.)
    """

    documents = load_resume_documents(user)

    if not documents:
        print("Resume not found.")
        return

    chunks = split_documents(documents)

    save_path = VECTORSTORE_DIR / "resume_indexes" / f"user_{user.id}"

    build_and_save(
        chunks,
        embeddings,
        save_path
    )

    print(f"Resume index built for User {user.id}")