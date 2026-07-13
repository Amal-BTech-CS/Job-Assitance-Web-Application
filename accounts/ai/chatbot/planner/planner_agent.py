import json

from accounts.ai.chatbot.core.resources import llm
from accounts.ai.chatbot.utils.patterns import SMALL_TALK_PATTERNS, ACKNOWLEDGEMENT_PATTERNS

# Safety net for planner misclassification: if the LLM returns "smalltalk"
# but the message clearly contains career/resume/job content, override it
# rather than silently swallowing a real question with a canned reply.
# Excludes pure courtesy phrasing so "thanks for the career advice!"
# doesn't get needlessly promoted back into a full agent run.
CONTENT_SIGNAL_WORDS = (
    "resume", "cv", "ats", "score", "job", "role", "salary",
    "interview", "certification", "roadmap", "skill", "project",
    "match", "apply", "application", "upskill", "career path",
)

COURTESY_WORDS = ("thank", "thanks", "bye", "goodbye")


def _looks_career_related(question):
    q = question.lower()
    if any(w in q for w in COURTESY_WORDS):
        return False
    return any(w in q for w in CONTENT_SIGNAL_WORDS)


SYSTEM_PROMPT = """
You are the Planner Agent of an AI Career Assistant.

Your ONLY responsibility is deciding which AI agent(s) should answer the user's question.

Never answer the question yourself.

---------------------------------------
AVAILABLE AGENTS
---------------------------------------

ATS
Use for:
- Resume vs Job comparison
- ATS score
- Missing skills
- Resume tailoring
- Resume optimization

RESUME
Use for:
- Resume review
- Resume summary
- Resume improvements
- Resume strengths
- Resume weaknesses
- Resume projects
- Resume experience
- Suitable roles

JOB
Use for:
- Job summary
- Job description
- Responsibilities
- Required skills
- Required technologies
- Salary
- Company expectations

CAREER
Use for:
- Career guidance
- Career roadmap
- Learning path
- Certifications
- Interview preparation
- AI trends
- Technology recommendations
- Upskilling

---------------------------------------

Rules

1. Return ONLY valid JSON.
2. Never explain your reasoning outside JSON.
3. Never answer the user's question.
4. Multiple agents are allowed.
5. Preserve order of importance.
6. If the message is a greeting, small talk, or not career-related,
   return {"agents": [], "type": "smalltalk"}
7. If the message asks to reformat, shorten, expand, re-list, or otherwise
   change the PRESENTATION of the assistant's PREVIOUS answer (e.g. "just
   give me 5 points", "make it shorter", "put that in a table") and is NOT
   asking for new information, return {"agents": [], "type": "followup"}.
   Only use this when conversation history is provided below AND the
   request is clearly about the previous answer's format, not new content.
8. Otherwise, return {"agents": [...], "type": "agents"}

Example:

{
    "agents":["ATS","RESUME"],
    "type": "agents",
    "reason":"The question requires resume analysis and ATS comparison."
}
"""


def create_plan(question, history=None):

    stripped = question.strip()

    # Unambiguous small talk — always safe to skip the LLM call.
    if SMALL_TALK_PATTERNS.match(stripped):
        return {"agents": [], "type": "smalltalk"}

    # Bare "ok"/"sure"/etc — only treat as small talk when there's no
    # history for it to be a follow-up to. With history, let the planner
    # LLM decide (it might be a truncated followup instruction).
    if not history and ACKNOWLEDGEMENT_PATTERNS.match(stripped):
        return {"agents": [], "type": "smalltalk"}

    history_block = ""
    if history:
        recent = history[-4:]
        history_block = "Recent conversation:\n" + "\n".join(
            f"{h['role']}: {h['content'][:300]}" for h in recent
        )

    prompt = f"""
{SYSTEM_PROMPT}

{history_block}

User Question:
{question}
"""

    response = llm.invoke(prompt)

    raw = response.content.strip()

    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        plan = json.loads(raw)

        if "agents" not in plan:
            raise ValueError()

        plan.setdefault("type", "agents")

        if plan["type"] == "smalltalk" and _looks_career_related(question):
            plan = {
                "agents": ["CAREER"],
                "type": "agents",
                "reason": "Safety net: message contains career-related "
                          "keywords, overriding smalltalk misclassification.",
            }

        return plan

    except Exception:

        return {
            "agents": ["CAREER"],
            "type": "agents",
            "reason": "Planner fallback."
        }