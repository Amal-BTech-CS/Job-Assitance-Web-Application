from accounts.ai.chatbot.core.resources import llm
from accounts.ai.chatbot.prompts.resume_prompt import RESUME_PROMPT


def analyze_resume(question, resume_retriever):
    """
    Analyze the logged-in user's resume.
    Expects a pre-built resume_retriever passed from chatbot.py via state.
    """

    if resume_retriever is None:
        return (
            "I couldn't find a resume in your profile. "
            "Please upload your resume first."
        )

    docs = resume_retriever.invoke(question)

    resume_context = "\n\n".join(
        doc.page_content
        for doc in docs
    )

    prompt = RESUME_PROMPT.format(
        resume_context=resume_context,
        question=question
    )

    response = llm.invoke(prompt)

    return response.content