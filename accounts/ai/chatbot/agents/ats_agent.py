from accounts.ai.chatbot.core.resources import (
    job_retriever,
    llm,
)

from accounts.ai.chatbot.prompts.ats_prompt import ATS_PROMPT


def analyze_ats(question, resume_retriever):
    """
    Compare user's resume against job descriptions using
    the module-level job_retriever (loaded once at startup).
    """

    if resume_retriever is None:
        return "No resume found. Please upload your resume first."

    resume_docs = resume_retriever.invoke(question)

    job_docs = job_retriever.invoke(question)

    resume_context = "\n\n".join(
        doc.page_content
        for doc in resume_docs
    )

    job_context = "\n\n".join(
        doc.page_content
        for doc in job_docs
    )

    prompt = ATS_PROMPT.format(
        resume_context=resume_context,
        job_context=job_context,
        question=question,
    )

    response = llm.invoke(prompt)

    return response.content