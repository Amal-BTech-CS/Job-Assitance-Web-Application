from accounts.ai.chatbot.core.resources import (
    llm,
    job_retriever,
)

from accounts.ai.chatbot.prompts.job_prompt import JOB_PROMPT


def analyze_job(question):
    """
    Analyze jobs using the permanent Job FAISS index.
    """

    docs = job_retriever.invoke(question)

    if not docs:
        return "I couldn't find any relevant job information."

    job_context = "\n\n".join(
        doc.page_content
        for doc in docs
    )

    prompt = JOB_PROMPT.format(
        job_context=job_context,
        question=question
    )

    response = llm.invoke(prompt)

    return response.content