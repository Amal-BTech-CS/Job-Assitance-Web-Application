from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_question(role, asked_questions):
    previous = "\n".join(asked_questions)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": f"""
Act as an interviewer.

Job Role:
{role}

Already asked:
{previous}

Generate ONE NEW interview question.

Rules:
- Ask simple and clear questions
- Maximum 20 words
- Ask only one concept at a time
- No multi-part questions
- Suitable for freshers/intermediate level
- Avoid repeating concepts
- Output only the question
"""
            }
        ]
    )

    return response.choices[0].message.content.strip()


def evaluate_answer(role, question, answer):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": f"""
You are a strict interview evaluator.

Job Role:
{role}

Question:
{question}

Candidate Answer:
{answer}

Rules:
- Evaluate ONLY candidate answer.
- Never invent that candidate answered.
- Treat these as no answer:
"", " ", "idk", "don't know",
"no ans", "skip", "pass".

Scoring:
0 = no answer
1-3 = incorrect
4-6 = partial
7-8 = good
9-10 = excellent

If score <= 3:
ALWAYS provide a correct answer.

Output exactly:

Score: X/10

Feedback:
(short explanation)

Improvement:
(how candidate can improve)

Correct Answer:
(provide ideal interview answer only if score <= 3)
"""
            }
        ]
    )

    return response.choices[0].message.content