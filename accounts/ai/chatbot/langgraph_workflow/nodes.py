import random

from accounts.ai.chatbot.core.resources import llm
from accounts.ai.chatbot.utils.patterns import SMALL_TALK_PATTERNS
from accounts.ai.chatbot.prompts.condense_prompt import CONDENSE_PROMPT
from accounts.ai.chatbot.prompts.followup_prompt import FOLLOWUP_PROMPT

from accounts.ai.chatbot.planner.planner_agent import create_plan

from accounts.ai.chatbot.agents.ats_agent import analyze_ats
from accounts.ai.chatbot.agents.resume_agent import analyze_resume
from accounts.ai.chatbot.agents.job_agent import analyze_job
from accounts.ai.chatbot.agents.career_agent import analyze_career

from accounts.ai.chatbot.synthesizer.synthesizer import synthesize


SMALLTALK_REPLIES = [
    "Hey! \U0001F44B How can I help with your career today?",
    "Hello! I'm here to help with your resume, job matches, or career guidance. What would you like to know?",
    "Hi there! Ask me anything about your resume or the available jobs. \U0001F60A",
    "Hey! Ready to help. You can ask me for an ATS score, resume review, missing skills, or career advice.",
    "Hello! What can I help you with today \u2014 resume, jobs, or career planning?",
]

GRATITUDE_REPLIES = [
    "Happy to help! Let me know if you have more questions. \U0001F60A",
    "Glad I could help! Anything else about your resume or career?",
    "You're welcome! Feel free to ask anything else.",
]

FAREWELL_REPLIES = [
    "Good luck with your job search! \U0001F680",
    "Best of luck! Come back anytime you need career help. \U0001F44B",
    "Take care! Hope you land that dream role. \U0001F31F",
]


def _get_smalltalk_reply(question):
    q = question.lower().strip()
    if any(w in q for w in ["thank", "thanks"]):
        return random.choice(GRATITUDE_REPLIES)
    if any(w in q for w in ["bye", "goodbye"]):
        return random.choice(FAREWELL_REPLIES)
    return random.choice(SMALLTALK_REPLIES)


# ==========================
# Planner Node
# ==========================

def planner_node(state):
    """
    Classifies the raw question (with recent history as context) into
    one of: smalltalk, followup (reformat the previous answer), or a
    real agents lookup. This runs BEFORE condensing, because a followup
    like "just give me 5 points" should never reach retrieval/agents at
    all -- condensing it into a full standalone question and re-running
    the CAREER agent would regenerate new content instead of reformatting
    what was already shown.
    """
    plan = create_plan(state["question"], state.get("history"))
    state["plan"] = plan
    return state


def route_after_planner(state):
    plan_type = state["plan"].get("type")

    if plan_type == "smalltalk":
        return "smalltalk"

    if plan_type == "followup":
        return "followup"

    return "condenser"


# ==========================
# Smalltalk Node
# ==========================

def smalltalk_node(state):
    state["standalone_question"] = state["question"]
    state["results"] = {"__smalltalk__": _get_smalltalk_reply(state["question"])}
    return state


# ==========================
# Followup Node
# ==========================

def followup_node(state):
    """
    Cheap path for requests that are purely about reformatting the
    previous answer (e.g. "just give me 5 points"). Reuses the last
    assistant message instead of re-running retrieval + agents, so the
    reformatted answer stays consistent with what the user already saw
    and costs a single lightweight LLM call instead of a full pass.
    """
    history = state.get("history") or []

    last_answer = next(
        (turn["content"] for turn in reversed(history) if turn["role"] == "assistant"),
        None,
    )

    state["standalone_question"] = state["question"]

    if not last_answer:
        # Planner shouldn't reach this branch without history, but guard
        # anyway -- there's no previous answer to reformat, and rerouting
        # to the agents here wouldn't do anything (this node's only
        # outgoing edge goes to the synthesizer, not the executor).
        state["results"] = {
            "__followup__": (
                "I don't have a previous answer to reformat yet -- "
                "what would you like to know?"
            )
        }
        return state

    prompt = FOLLOWUP_PROMPT.format(
        previous_answer=last_answer,
        instruction=state["question"],
    )

    response = llm.invoke(prompt)
    state["results"] = {"__followup__": response.content.strip()}
    return state


# ==========================
# Condense Node
# ==========================

def condense_node(state):
    """
    Rewrites referential questions (e.g. "what about the second one?")
    into standalone questions using recent conversation history, so
    that retrieval has a self-contained query to search against. Only
    reached for questions the planner has already classified as needing
    a real agent lookup.
    """
    question = state["question"]
    history = state.get("history") or []

    if not history:
        state["standalone_question"] = question
        return state

    history_text = "\n".join(
        f"{turn['role'].capitalize()}: {turn['content']}"
        for turn in history
    )

    prompt = CONDENSE_PROMPT.format(
        history=history_text,
        question=question,
    )

    response = llm.invoke(prompt)
    rewritten = response.content.strip().strip('"')

    state["standalone_question"] = rewritten if rewritten else question
    return state


# ==========================
# Execution Node
# ==========================

def execution_node(state):
    question = state["standalone_question"]
    plan = state["plan"]
    resume_retriever = state["resume_retriever"]

    results = {}

    if "ATS" in plan.get("agents", []):
        results["ATS"] = analyze_ats(
            question=question,
            resume_retriever=resume_retriever,
        )

    if "RESUME" in plan.get("agents", []):
        results["RESUME"] = analyze_resume(
            question=question,
            resume_retriever=resume_retriever,
        )

    if "JOB" in plan.get("agents", []):
        results["JOB"] = analyze_job(
            question=question,
        )

    if "CAREER" in plan.get("agents", []):
        results["CAREER"] = analyze_career(
            question=question,
            resume_retriever=resume_retriever,
        )

    state["results"] = results
    return state


# ==========================
# Synthesizer Node
# ==========================

def synthesizer_node(state):
    results = state["results"]

    # Smalltalk / followup already produced the final text -- return directly,
    # no synthesis LLM call needed.
    if "__smalltalk__" in results:
        state["final_answer"] = results["__smalltalk__"]
        return state

    if "__followup__" in results:
        state["final_answer"] = results["__followup__"]
        return state

    answer = synthesize(
        question=state["standalone_question"],
        responses=results,
    )

    state["final_answer"] = answer

    print(state["plan"])
    return state