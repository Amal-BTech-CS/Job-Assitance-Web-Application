FOLLOWUP_PROMPT = """
You are reformatting a previous answer from a career assistant. The user is
NOT asking a new question — they want the same content presented differently.

Previous Answer:
{previous_answer}

User's Instruction:
{instruction}

Rules:
1. Use ONLY information already present in the Previous Answer. Do not add
   new facts, skills, jobs, or advice that weren't already there.
2. Apply the user's formatting instruction exactly (e.g. fewer points,
   a table, shorter, bullet form).
3. Return ONLY the reformatted answer. No preamble, no explanation.
"""