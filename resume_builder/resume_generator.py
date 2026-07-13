"""
resume_generator.py
--------------------
Builds the prompt sent to the LLM, calls it, parses/validates the JSON
response, and returns a clean resume dict for use in templates and
the docx/pdf exporters.
"""

import json
from .llm_client import chat_completion


class ResumeValidationError(Exception):
    """Raised when input or AI output fails validation."""
    pass


SYSTEM_PROMPT = """You are a professional resume writer. Given raw information
about a candidate, produce a polished, ATS-friendly resume as JSON only,
with exactly these keys:

"summary": string (3-4 sentences, professional tone)
"skills": array of strings (individual skill names only, no sentences)
"experience": array of objects, each with "title", "company", "duration",
              and "bullets" (array of short achievement-focused strings)
"education": array of strings
"certifications": array of strings

Return ONLY valid JSON. No markdown formatting, no code fences, no extra text."""


def _build_user_prompt(form_data: dict) -> str:
    return (
        f"Full Name: {form_data['full_name']}\n"
        f"Target Title: {form_data.get('target_title', '')}\n"
        f"Summary notes: {form_data.get('summary', '')}\n"
        f"Skills: {form_data.get('skills', '')}\n"
        f"Experience: {form_data.get('experience', '')}\n"
        f"Education: {form_data.get('education', '')}\n"
        f"Certifications: {form_data.get('certifications', '')}\n"
    )


def generate_resume(form_data: dict) -> dict:
    if not form_data.get("full_name"):
        raise ResumeValidationError("Full name is required.")
    if not form_data.get("experience"):
        raise ResumeValidationError("Experience is required.")

    user_prompt = _build_user_prompt(form_data)

    try:
        raw = chat_completion(SYSTEM_PROMPT, user_prompt, json_mode=True)
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise ResumeValidationError("AI returned invalid JSON. Please try again.")
    except Exception as e:
        raise ResumeValidationError(f"AI generation failed: {e}")

    resume = {
        "full_name": form_data["full_name"],
        "target_title": form_data.get("target_title", ""),
        "email": form_data.get("email", ""),
        "phone": form_data.get("phone", ""),
        "location": form_data.get("location", ""),
        "linkedin": form_data.get("linkedin", ""),
        "website": form_data.get("website", ""),
        "summary": data.get("summary", form_data.get("summary", "")),
        "skills": data.get("skills", []),
        "experience": data.get("experience", []),
        "education": data.get("education", []),
        "certifications": data.get("certifications", []),
    }

    return resume