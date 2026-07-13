import json
import re

from accounts.ai.chatbot.core.resources import llm


# Greetings and small talk — handle directly, no agent needed
SMALL_TALK_PATTERNS = re.compile(
    r"^\s*(hi+|hello+|hey+|howdy|good\s*(morning|afternoon|evening|night)|"
    r"what'?s up|sup|greetings|hiya|yo|namaste|how are you|how r u|"
    r"thank(s| you)|bye|goodbye|ok|okay|cool|great|nice|got it|sure)\s*[!?.]*\s*$",
    re.IGNORECASE
)

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

Example:

{
    "agents":["ATS","RESUME"],
    "reason":"The question requires resume analysis and ATS comparison."
}
"""


def create_plan(question):

    # Fast-path: detect small talk locally without calling the LLM
    if SMALL_TALK_PATTERNS.match(question.strip()):
        return {"agents": [], "type": "smalltalk"}

    prompt = f"""
{SYSTEM_PROMPT}

User Question:
{question}
"""

    response = llm.invoke(prompt)

    print("========== Planner Raw Response ==========")
    print(response.content)
    print("==========================================")

    try:
        plan = json.loads(response.content)

        if "agents" not in plan:
            raise ValueError()

        return plan

    except Exception:

        return {
            "agents": ["CAREER"],
            "reason": "Planner fallback."
        }