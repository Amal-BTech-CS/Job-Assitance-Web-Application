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
import pdfplumber
from groq import Groq
import json
import os

from dotenv import load_dotenv



# ==========================
# Extract Resume Text
# ==========================

def extract_resume_text(file):

    file.seek(0)

    with pdfplumber.open(file) as pdf:
        text = ""

        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    return text




# ==========================
# Groq Setup
# ==========================


load_dotenv()


client = Groq(

    api_key=os.getenv(
        "GROQ_API_KEY"
    )

)





# ==========================
# Resume Analysis
# ==========================


def analyze_resume(text):


    prompt = f"""


You are an expert AI resume parser and recruiter.


Analyze the resume and return ONLY valid JSON.


Rules:

1. Return ONLY JSON.
2. No explanation.
3. Missing values should be empty string.
4. Extract LinkedIn and Github if available.
5. Extract all skills.
6. Extract all work experiences.
7. Do not include experience description.
8. The dates should be completed no short forms

==========================
EDUCATION RULES
==========================


Find all education qualifications internally.


Return ONLY the highest qualification.


Set level using only these values:


Doctorate

Post Graduate

Graduate

Diploma

Higher Secondary

Secondary



Priority:


Doctorate:

PhD
Doctorate
DPhil



Post Graduate:

M.Tech
M.E
MBA
MCA
M.Sc
M.Com
MA
Master Degree



Graduate:

B.Tech
B.E
BCA
B.Sc
B.Com
BA
Bachelor Degree



Diploma:

Diploma courses



Higher Secondary:

12th
Plus Two



Secondary:

10th
SSLC



Examples:


B.Tech + M.Tech

Return:


degree:
M.Tech Computer Science

level:
Post Graduate




B.Sc only


Return:


degree:
B.Sc Computer Science

level:
Graduate




PhD


Return:

degree:
PhD Computer Science

level:
Doctorate

Never return lower qualifications if higher qualification exists.

Return JSON exactly:

{{

"name":"",

"email":"",

"phone":"",

"linkedin":"",

"github":"",

"skills":[],

"education":{{

    "degree":"",

    "level":"",

    "college":"",

    "percentage":"",

    "start_year":"",

    "end_year":""

}},


"experience":[

{{

"job_title":"",

"company":"",

"start_date":"",

"end_date":""

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

            "role":"user",

            "content":prompt

            }
        ]
    )
    result = response.choices[0].message.content


    try:


        result = result.replace(

            "```json",

            ""

        )


        result = result.replace(

            "```",

            ""

        )



        return json.loads(

            result.strip()

        )



    except Exception as e:


        print(
            "JSON ERROR:",
            e
        )


        return {}