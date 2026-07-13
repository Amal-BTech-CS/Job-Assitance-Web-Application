from groq import Groq
import os
import re
import time

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def generate_quiz(topic, difficulty, count):
    prompt = f"""
Generate {count} MCQ questions.

Topic: {topic}
Difficulty: {difficulty}

Format:

Q1:
Question

A) option
B) option
C) option
D) option

Answer: A

Generate ONLY the quiz in this format.
"""

    quiz = None

    for attempt in range(5):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )

            quiz = response.choices[0].message.content
            break

        except Exception:
            time.sleep(2 ** attempt)

    return quiz


def parse_quiz(quiz_text):
    questions = re.split(r"\n(?=Q\d+:)", quiz_text)
    parsed = []

    for q in questions:
        if not q.strip():
            continue

        match = re.search(r"Answer:\s*([A-D])", q)
        if not match:
            continue

        parsed.append({
            "question": re.sub(r"\nAnswer:\s*[A-D]", "", q),
            "answer": match.group(1)
        })

    return parsed