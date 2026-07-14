import os
import pdfplumber
from groq import Groq
from dotenv import load_dotenv
import tempfile
import shutil

# -----------------------------
# Load Environment Variables
# -----------------------------
load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    raise ValueError("GROQ_API_KEY not found in .env file")

client = Groq(api_key=API_KEY)


# -----------------------------
# Extract Resume Text
# -----------------------------
def extract_resume_text(pdf_file):
    """
    pdf_file can be:
      - a local path string (kept for backwards compatibility)
      - a Django FieldFile (e.g. resume.resume_file, backed by S3 or local disk)
      - an UploadedFile / InMemoryUploadedFile (freshly uploaded, not saved yet)

    We no longer assume it's always a local filesystem path, since resumes
    can now live on S3 via the default storage backend.
    """
    text = ""

    # Rewind if it's a file-like object, so we always read from the start
    # even if something else touched the stream before us.
    if hasattr(pdf_file, "seek"):
        pdf_file.seek(0)

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    # Rewind again so the caller can still save/re-read this same file
    # afterwards (e.g. to attach it to an Application).
    if hasattr(pdf_file, "seek"):
        pdf_file.seek(0)

    return text


# -----------------------------
# Generate Cover Letter
# -----------------------------
def generate_cover_letter(resume_file, job_title, company_name):

    resume_text = extract_resume_text(resume_file)

    prompt = f"""
You are an expert career coach and cover letter writer.

Generate a professional ATS-friendly cover letter.

Use ONLY information available in the resume.

JOB TITLE:
{job_title}

COMPANY:
{company_name}

RESUME:
{resume_text}

Instructions:
- Extract candidate details from resume.
- Use the candidate's name from the resume.
- Mention relevant skills, education, and projects.
- Align the experience with the job title.
- Keep the cover letter between 100 and 200 words.
- Maintain a professional tone.
- Do NOT invent achievements or experiences.
- Return ONLY the cover letter.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a professional ATS cover letter writer."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.7,
        max_tokens=500
    )

    return response.choices[0].message.content