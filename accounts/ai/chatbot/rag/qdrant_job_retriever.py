# accounts/ai/chatbot/rag/qdrant_job_retriever.py
from langchain_core.documents import Document

from accounts.ai.recommender.vector_db import client, COLLECTION_NAME, ensure_collection
from accounts.ai.recommender.embedding import get_embedding
from accounts.models import Job


class QdrantJobRetriever:
    def __init__(self, k=8):
        self.k = k

    def invoke(self, query):
        ensure_collection()
        vector = get_embedding(query)
        hits = client.query_points(
            collection_name=COLLECTION_NAME,
            query=vector.tolist(),
            limit=self.k,
            with_payload=True,
        ).points

        job_ids = [h.payload["job_id"] for h in hits if h.payload]
        jobs = {j.id: j for j in Job.objects.filter(id__in=job_ids).select_related("company")}

        return [
            Document(
                page_content=(
                    f"Job Title: {j.title}\nCompany: {j.company.company_name}\n"
                    f"Location: {j.location}\nSalary: {j.salary}\n"
                    f"Description:\n{j.description}"
                ),
                metadata={"job_id": j.id, "source": "job"},
            )
            for jid in job_ids if (j := jobs.get(jid))
        ]