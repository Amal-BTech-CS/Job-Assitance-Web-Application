from accounts.ai.chatbot.langgraph_workflow.graph import graph

from accounts.ai.chatbot.rag.temp_resume_retriever import (
    get_resume_retriever
)

from accounts.ai.chatbot.core.resources import (
    job_retriever
)


def _filter_informative_history(history):
    """
    Drop canned smalltalk turns before they reach the planner/condenser.
    They carry no real content, and feeding them back in can bias the
    next classification toward smalltalk too (a generic "ask me
    anything!" reply sitting in the history makes the next real
    question look like part of idle chit-chat). Followup turns are kept
    since their content is real -- just reformatted.
    """
    return [
        turn for turn in history
        if turn.get("role") != "assistant" or turn.get("type") != "smalltalk"
    ]


def ask(user, question, history=None):
    """
    Main entry point for the AI Career Assistant.

    Parameters
    ----------
    user : Django User
        Logged-in user.

    question : str
        User's question.

    history : list[dict], optional
        Recent conversation turns, most-recent-last:
        [{"role": "user", "content": "..."},
         {"role": "assistant", "content": "...", "type": "agents"}, ...]
        The "type" on assistant turns (set from the returned plan_type)
        lets this filter out uninformative smalltalk turns before they
        reach the planner. Caller (the view) owns where this is stored.

    Returns
    -------
    dict
        {"answer": str, "plan_type": str} -- plan_type should be saved
        alongside the answer in history so future turns can filter on it.
    """

    # -------------------------------
    # Build temporary Resume Retriever
    # -------------------------------

    resume_retriever = get_resume_retriever(user)

    if resume_retriever is None:

        return {
            "answer": (
                "I couldn't find your resume. "
                "Please upload your resume before using the AI Career Assistant."
            ),
            "plan_type": "smalltalk",
        }

    # -------------------------------
    # Initial LangGraph State
    # -------------------------------

    state = {

        "user": user,

        "question": question,

        "history": _filter_informative_history(history or []),

        "standalone_question": "",

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
    # Return final response + classification
    # -------------------------------

    return {
        "answer": result["final_answer"],
        "plan_type": result.get("plan", {}).get("type", "agents"),
    }