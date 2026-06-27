import pdfplumber
from groq import Groq
import json,os
from dotenv import load_dotenv
def extract_resume_text(file_path):

    text = ""

    with pdfplumber.open(file_path) as pdf:

        for page in pdf.pages:

            text += page.extract_text() or ""

    return text




load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)
def analyze_resume(text):

    prompt = f"""
    You are an expert recruiter and resume parser.

    Analyze the resume and return ONLY valid JSON.

    Rules:

    1. Return ONLY valid JSON.
    2. Do not include explanations.
    3. Extract LinkedIn URL if available.
    4. Extract GitHub URL if available.
    5. If any field is missing, return an empty string.
    6. Extract ALL education details found in the resume.
    7. Each education must have an education_type:
    - "10th"
    - "plus_two"
    - "degree"
    8. If the resume contains only Degree, return only Degree.
    Do NOT invent 10th or Plus Two.
    9. If multiple degrees exist, classify each correctly.

    Return JSON exactly in this format:

    {{
        "name": "",
        "email": "",
        "phone": "",
        "linkedin": "",
        "github": "",
        "summary": "",

        "skills": {{
            "programming_languages": [],
            "ai_ml": [],
            "data_science": [],
            "databases": [],
            "tools": []
        }},

        "education": [
            {{
                "education_type": "10th",
                "degree": "",
                "college": "",
                "cgpa": "",
                "start_year": "",
                "end_year": ""
            }},
            {{
                "education_type": "plus_two",
                "degree": "",
                "college": "",
                "cgpa": "",
                "start_year": "",
                "end_year": ""
            }},
            {{
                "education_type": "degree",
                "degree": "",
                "college": "",
                "cgpa": "",
                "start_year": "",
                "end_year": ""
            }}
        ],

        "experience": [
            {{
                "job_title": "",
                "company": "",
                "start_date": "",
                "end_date": "",
                "description": ""
            }}
        ]
    }}

    Resume:

    {text}
    """

    response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {
            "role": "user",
            "content": prompt
        }
    ]
    )

    result = response.choices[0].message.content

    print("RAW AI RESPONSE:")
    print(result)

    try:
        result = result.replace("```json", "")
        result = result.replace("```", "")
        result = result.strip()

        return json.loads(result)

    except Exception as e:
        print("JSON ERROR:", e)
    return {}