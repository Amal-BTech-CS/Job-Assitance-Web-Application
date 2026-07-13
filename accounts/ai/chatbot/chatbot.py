from accounts.ai.chatbot.langgraph_workflow.graph import graph

from accounts.ai.chatbot.rag.temp_resume_retriever import (
    get_resume_retriever
)

from accounts.ai.chatbot.core.resources import (
    job_retriever
)


def ask(user, question):
    """
    Main entry point for the AI Career Assistant.

    Parameters
    ----------
    user : Django User
        Logged-in user.

    question : str
        User's question.

    Returns
    -------
    str
        Final chatbot response.
    """

    # -------------------------------
    # Build temporary Resume Retriever
    # -------------------------------

    resume_retriever = get_resume_retriever(user)

    if resume_retriever is None:

        return (
            "I couldn't find your resume. "
            "Please upload your resume before using the AI Career Assistant."
        )

    # -------------------------------
    # Initial LangGraph State
    # -------------------------------

    state = {

        "user": user,

        "question": question,

        "plan": {},

        "resume_retriever": resume_retriever,

        "job_retriever": job_retriever,

        "results": {},

        "final_answer": ""

    }

    # -------------------------------
    # Execute LangGraph
    # -------------------------------

    result = graph.invoke(state)

    # -------------------------------
    # Return final response
    # -------------------------------

    return result["final_answer"]