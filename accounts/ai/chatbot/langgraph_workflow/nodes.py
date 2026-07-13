import random

from accounts.ai.chatbot.planner.planner_agent import create_plan

from accounts.ai.chatbot.agents.ats_agent import analyze_ats
from accounts.ai.chatbot.agents.resume_agent import analyze_resume
from accounts.ai.chatbot.agents.job_agent import analyze_job
from accounts.ai.chatbot.agents.career_agent import analyze_career

from accounts.ai.chatbot.synthesizer.synthesizer import synthesize


SMALLTALK_REPLIES = [
    "Hey! 👋 How can I help with your career today?",
    "Hello! I'm here to help with your resume, job matches, or career guidance. What would you like to know?",
    "Hi there! Ask me anything about your resume or the available jobs. 😊",
    "Hey! Ready to help. You can ask me for an ATS score, resume review, missing skills, or career advice.",
    "Hello! What can I help you with today — resume, jobs, or career planning?",
]

GRATITUDE_REPLIES = [
    "Happy to help! Let me know if you have more questions. 😊",
    "Glad I could help! Anything else about your resume or career?",
    "You're welcome! Feel free to ask anything else.",
]

FAREWELL_REPLIES = [
    "Good luck with your job search! 🚀",
    "Best of luck! Come back anytime you need career help. 👋",
    "Take care! Hope you land that dream role. 🌟",
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
    question = state["question"]
    plan = create_plan(question)
    state["plan"] = plan
    return state


# ==========================
# Execution Node
# ==========================

def execution_node(state):
    question = state["question"]
    plan = state["plan"]
    resume_retriever = state["resume_retriever"]

    # Small talk — no agents needed, reply directly
    if plan.get("type") == "smalltalk" or not plan.get("agents"):
        state["results"] = {"__smalltalk__": _get_smalltalk_reply(question)}
        return state

    results = {}

    if "ATS" in plan["agents"]:
        results["ATS"] = analyze_ats(
            question=question,
            resume_retriever=resume_retriever,
        )

    if "RESUME" in plan["agents"]:
        results["RESUME"] = analyze_resume(
            question=question,
            resume_retriever=resume_retriever,
        )

    if "JOB" in plan["agents"]:
        results["JOB"] = analyze_job(
            question=question,
        )

    if "CAREER" in plan["agents"]:
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

    # If it's a smalltalk reply, return it directly — no LLM synthesis needed
    if "__smalltalk__" in results:
        state["final_answer"] = results["__smalltalk__"]
        return state

    answer = synthesize(
        question=state["question"],
        responses=results,
    )

    state["final_answer"] = answer
    return state