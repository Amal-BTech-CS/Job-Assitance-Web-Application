from typing import Any, TypedDict


class GraphState(TypedDict):
    """
    Shared state passed between LangGraph nodes.
    """

    # Logged-in Django user
    user: Any

    # User's current question
    question: str

    # Planner output
    plan: dict

    # Temporary resume retriever (built at chat start)
    resume_retriever: Any

    # Permanent job retriever
    job_retriever: Any

    # Responses from executed agents
    results: dict

    # Final synthesized response
    final_answer: str