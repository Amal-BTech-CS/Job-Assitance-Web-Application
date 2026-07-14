import pdfplumber
from groq import Groq
from dotenv import load_dotenv
import json
import os


# ============================================
# Extract Resume Text
# ============================================

def extract_resume_text(file_path):

    text = ""

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""

    return text


# ============================================
# Load Groq
# ============================================

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


# ============================================
# Resume Parser
# ============================================

def analyze_resume(text):

    prompt = f"""
You are an expert Resume Parser.

Extract information from the resume.

Return ONLY valid JSON.

Rules:

1. Return ONLY JSON.
2. No markdown.
3. No explanation.
4. Missing values should be "".
5. Extract ALL skills.
6. Extract ALL work experience.
7. Extract ALL projects.
8. Extract Github and LinkedIn if available.
9. Return only the HIGHEST education qualification and the percentage or CGPA as in the resume.

-------------------------------------------------

Education Level must be one of:

Doctorate
Post Graduate
Graduate
Diploma
Higher Secondary
Secondary

Examples

PhD
-> Doctorate

M.Tech
MBA
MCA
MSc
MA
M.Com
-> Post Graduate

B.Tech
BE
BCA
BSc
BCom
BA
-> Graduate

Diploma
-> Diploma

12th
Plus Two
-> Higher Secondary

10th
SSLC
-> Secondary

-------------------------------------------------

Return JSON in EXACTLY this format.

{{
    "personal_information":
    {{
        "name":"",
        "email":"",
        "phone":"",
        "linkedin":"",
        "github":""
    }},

    "summary":"",

    "skills":[
        {{
            "skill_name":""
        }}
    ],

    "education":
    {{
        "qualification_level":"",
        "degree":"",
        "college":"",
        "cgpa":"",
        "start_year":"",
        "end_year":""
    }},

    "experience":
    [
        {{
            "job_title":"",
            "company":"",
            "start_date":"",
            "end_date":""
        }}
    ],

    "projects":
    [
        {{
            "title":"",
            "description":"",
            "technologies":"",
            "github_link":""
        }}
    ]
}}

Resume

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

    try:

        result = (
            result.replace("```json", "").replace("```", "").strip()
        )

        return json.loads(result)

    except Exception as e:

        print("JSON Parsing Error:", e)

        return {}