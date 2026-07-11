from accounts.ai.chatbot.core.resources import llm
from accounts.ai.chatbot.prompts.career_prompt import CAREER_PROMPT


def analyze_career(question, resume_retriever):
    """
    Provide personalized career guidance based on
    the logged-in user's resume.
    """

    if resume_retriever is None:
        return (
            "I couldn't find your resume. "
            "Please upload your resume first."
        )

    docs = resume_retriever.invoke(question)

    resume_context = "\n\n".join(
        doc.page_content
        for doc in docs
    )

    prompt = CAREER_PROMPT.format(
        resume_context=resume_context,
        question=question
    )

    response = llm.invoke(prompt)

    return response.content