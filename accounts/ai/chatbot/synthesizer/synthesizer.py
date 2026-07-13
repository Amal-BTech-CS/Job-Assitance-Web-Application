from accounts.ai.chatbot.llm.groq_client import get_llm
from accounts.ai.chatbot.prompts.synthesizer_prompt import SYNTHESIZER_PROMPT

llm = get_llm()


def synthesize(question, responses):
    """
    Combine responses from multiple agents into a
    single coherent response.

    If only one agent responded, return it directly
    without calling the LLM again.
    """

    # No response from any agent
    if not responses:
        return "I couldn't generate a response."

    # Only one agent responded
    if len(responses) == 1:
        return next(iter(responses.values()))

    # Multiple agents responded
    agent_outputs = ""

    for agent_name, response in responses.items():

        agent_outputs += f"""
=========================
{agent_name} AGENT
=========================

{response}

"""

    prompt = SYNTHESIZER_PROMPT.format(
        question=question,
        agent_outputs=agent_outputs
    )

    response = llm.invoke(prompt)

    return response.content