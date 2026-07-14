import re


# Unambiguous greetings/farewells/gratitude — always safe to fast-path,
# regardless of history, since these are never a follow-up instruction.
SMALL_TALK_PATTERNS = re.compile(
    r"^\s*(hi+|hello+|hey+|howdy|good\s*(morning|afternoon|evening|night)|"
    r"what'?s up|sup|greetings|hiya|yo|namaste|how are you|how r u|"
    r"thank(s| you)|bye|goodbye)\s*[!?.]*\s*$",
    re.IGNORECASE
)

# Bare acknowledgements — ambiguous. "ok" as a first message is small talk,
# but "ok" right after a real answer could mean "ok, now shorten that" was
# cut short, or genuinely just be closing the topic. Only fast-path these
# when there's no history to be a follow-up to; otherwise let the planner
# LLM decide with context.
ACKNOWLEDGEMENT_PATTERNS = re.compile(
    r"^\s*(ok|okay|cool|great|nice|got it|sure)\s*[!?.]*\s*$",
    re.IGNORECASE
)