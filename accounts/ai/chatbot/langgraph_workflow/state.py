from typing import Any, TypedDict


class GraphState(TypedDict):
    """
    Shared state passed between LangGraph nodes.
    """

    # Logged-in Django user
    user: Any

    # User's current question, exactly as typed
    question: str

    # Recent turns: [{"role": "user"|"assistant", "content": str}, ...]
    history: list

    # `question` rewritten to resolve references to prior turns
    # (e.g. "what about the second one?" -> "Tell me more about the
    # Backend Developer role at Acme Corp"). Used for planning + retrieval.
    standalone_question: str

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