CONDENSE_PROMPT = """
You rewrite follow-up messages into standalone questions for a career assistant.

Conversation History:
{history}

New Message:
{question}

Rules:
1. If the New Message references something from the history (e.g. "the second one",
   "that job", "it", "what about..."), rewrite it into a standalone question that
   includes the specific thing being referenced (job title, skill, section, etc.).
2. If the New Message is already standalone and needs no history to understand,
   return it EXACTLY unchanged.
3. Never answer the question. Only rewrite it.
4. Return ONLY the rewritten question. No quotes, no explanation, no prefix.
"""