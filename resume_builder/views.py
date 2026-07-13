from django.shortcuts import render

# Create your views here.
import json
import re

from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import render_to_string
from groq import Groq
from weasyprint import HTML

from .models import Resume
from .resume_generator import generate_resume, ResumeValidationError


client = Groq(api_key=settings.GROQ_API_KEY)


# ---------------------------------------------------------------------------
# Small helpers for turning raw textarea text into clean lists (and back)
# ---------------------------------------------------------------------------

# Phrases that indicate a chunk is sentence filler, not an actual skill
FILLER_PREFIXES = (
    "skilled in", "experience in", "experienced in", "proficient in",
    "expertise in", "knowledge of", "familiar with", "strong in",
    "background in", "worked with", "skills include", "skill set",
    "including", "such as", "as well as", "with experience in",
)


def _skills_to_list(raw):
    """
    Splits skills text on commas, newlines, AND periods, so mixed input like:
    'Python, SQL, TensorFlow, and MySQL. Skilled in data analysis, ML'
    still produces clean individual tags instead of merging sentences together.
    Drops sentence-filler chunks (e.g. "Skilled in data analysis").
    Preserves the exact casing of real skill text (no capitalization changes).
    Removes duplicate skills while preserving the original order.
    """
    if not raw:
        return []

    # Treat newlines and periods as separators too, alongside commas
    normalized = raw.replace("\n", ",").replace(".", ",")
    parts = re.split(r",", normalized)

    skills = []
    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Strip a leading "and " that often survives from sentence-style input
        if part.lower().startswith("and "):
            part = part[4:].strip()
        if not part:
            continue

        # Drop chunks that are sentence filler, not real skills
        if part.lower().startswith(FILLER_PREFIXES):
            continue

        skills.append(part)

    # Remove duplicates while preserving order
    unique_skills = []
    for skill in skills:
        if skill not in unique_skills:
            unique_skills.append(skill)

    return unique_skills


def _skills_to_text(skills):
    """
    Rebuilds the skills list into a single normalized comma-separated string,
    e.g. "Python, SQL, TensorFlow, ML" — regardless of how the user originally
    typed it (line-by-line, periods, mixed, etc). This is the pattern shown
    back in the edit textbox after Save.
    """
    return ", ".join(skills or [])


def _lines_to_list(raw):
    """One item per non-empty line."""
    if not raw:
        return []
    return [line.strip() for line in raw.splitlines() if line.strip()]


def _lines_to_text(lines):
    return "\n".join(lines or [])


def _certs_to_list(raw):
    """Same as _lines_to_list but strips a leading '*' or '-' bullet marker."""
    if not raw:
        return []
    out = []
    for line in raw.splitlines():
        line = line.strip().lstrip("*-").strip()
        if line:
            out.append(line)
    return out


def _experience_to_text(experience):
    """
    [{"role_line": "Engineer — Acme", "bullets": ["Did X", "Did Y"]}, ...]
    -> "Engineer — Acme\n- Did X\n- Did Y\n\n<next job>"
    """
    blocks = []
    for job in experience or []:
        lines = [job.get("role_line", "")]
        for bullet in job.get("bullets", []):
            lines.append(f"- {bullet}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def _text_to_experience(raw):
    """
    Reverse of _experience_to_text. Jobs are separated by a blank line.
    The first non-bullet line of a block is the role line; every line
    starting with '-' or '*' is a bullet.
    """
    if not raw:
        return []

    experience = []
    blocks = [b for b in raw.replace("\r\n", "\n").split("\n\n") if b.strip()]
    for block in blocks:
        role_line = ""
        bullets = []
        for line in block.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith(("-", "*", "•")):
                bullets.append(line.lstrip("-*•").strip())
            elif not role_line:
                role_line = line
            else:
                bullets.append(line)
        if role_line or bullets:
            experience.append({"role_line": role_line, "bullets": bullets})
    return experience


# ---------------------------------------------------------------------------
# Step 1: the intake form
# ---------------------------------------------------------------------------

def resume_builder(request):
    """Display the resume builder form (raw notes)."""
    return render(request, "accounts/resume_builder/resume_builder.html", {
        "form_data": request.session.get("form_data", {})
    })


def generate_resume_with_ai(form_data):
    """
    Ask the AI to polish only the Summary and Experience sections.
    Returns a dict: {"summary": "...", "experience": [{"role_line": "...", "bullets": [...]}]}
    """

    prompt = f"""
You are an expert resume writer. Rewrite the candidate's raw notes into an
ATS-friendly resume format. Return ONLY valid JSON, no markdown, no backticks,
no preamble. Use this exact structure:

{{
  "summary": "A 3-4 sentence results-oriented professional summary.",
  "experience": [
    {{
      "role_line": "Job Title — Company Name, Location (Start – End)",
      "bullets": ["Achievement bullet 1", "Achievement bullet 2", "Achievement bullet 3"]
    }}
  ]
}}

Rules:
- Do not invent facts, companies, or numbers that are not implied by the raw text.
- Each bullet should start with a strong action verb and be results-focused where possible.
- If multiple jobs are described in the raw experience text, split them into separate objects in the "experience" list.
- Keep bullets concise (under 25 words each).

Target Job Title: {form_data.get('target_title')}

Candidate's raw summary notes:
{form_data.get('summary_notes')}

Candidate's raw experience notes:
{form_data.get('experience_raw')}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a professional resume writing assistant. You always return valid JSON only."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=1200,
        temperature=0.6,
    )

    raw_text = response.choices[0].message.content.strip()

    # Strip accidental markdown code fences if the model adds them
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        if raw_text.lower().startswith("json"):
            raw_text = raw_text[4:].strip()

    return json.loads(raw_text)


# ---------------------------------------------------------------------------
# Step 2: generate with AI -> land on the Edit page
# ---------------------------------------------------------------------------

def resume_generator(request):
    """Process the intake form, call the AI, and hand off to the edit page."""

    if request.method != "POST":
        return redirect("resume_builder")

    form_data = {
        "full_name": request.POST.get("full_name", "").strip(),
        "target_title": request.POST.get("target_title", "").strip(),
        "email": request.POST.get("email", "").strip(),
        "phone": request.POST.get("phone", "").strip(),
        "location": request.POST.get("location", "").strip(),
        "linkedin": request.POST.get("linkedin", "").strip(),
        "website": request.POST.get("website", "").strip(),
        "summary_notes": request.POST.get("summary_notes", ""),
        "skills_raw": request.POST.get("skills_raw", ""),
        "experience_raw": request.POST.get("experience_raw", ""),
        "education_raw": request.POST.get("education_raw", ""),
        "certifications_raw": request.POST.get("certifications_raw", ""),
    }
    request.session["form_data"] = form_data

    if not form_data["full_name"]:
        messages.error(request, "Full name is required.")
        return redirect("resume_builder")
    if not form_data["experience_raw"]:
        messages.error(request, "Please describe at least one role in Work experience.")
        return redirect("resume_builder")

    summary = ""
    experience = []
    skills = _skills_to_list(form_data["skills_raw"])
    education = _lines_to_list(form_data["education_raw"])
    certifications = _certs_to_list(form_data["certifications_raw"])

    try:
        # resume_generator.py expects generic text fields, so map our
        # "_raw" intake fields onto the keys it looks for.
        generator_input = {
            "full_name": form_data["full_name"],
            "target_title": form_data["target_title"],
            "email": form_data["email"],
            "phone": form_data["phone"],
            "location": form_data["location"],
            "linkedin": form_data["linkedin"],
            "website": form_data["website"],
            "summary": form_data["summary_notes"],
            "skills": form_data["skills_raw"],
            "experience": form_data["experience_raw"],
            "education": form_data["education_raw"],
            "certifications": form_data["certifications_raw"],
        }
        ai_data = generate_resume(generator_input)
        summary = ai_data.get("summary", "")

        # Adapt resume_generator.py's experience schema
        # ({"title","company","duration","bullets"}) to the
        # {"role_line","bullets"} schema the edit page / PDF expect.
        for job in ai_data.get("experience", []):
            role_bits = [job.get("title", ""), job.get("company", "")]
            role_line = " — ".join(b for b in role_bits if b)
            if job.get("duration"):
                role_line = f"{role_line} ({job['duration']})" if role_line else job["duration"]
            experience.append({"role_line": role_line, "bullets": job.get("bullets", [])})

        if ai_data.get("skills"):
            skills = ai_data["skills"]
        if ai_data.get("education"):
            education = ai_data["education"]
        if ai_data.get("certifications"):
            certifications = ai_data["certifications"]

        messages.success(request, "Resume generated! Review and edit it below before saving.")
    except ResumeValidationError as e:
        messages.error(request, str(e))
    except Exception as e:
        messages.error(
            request,
            f"AI generation failed ({e}). You can still write the summary and "
            f"experience bullets yourself below.",
        )

    # Build the working resume record that the edit page will operate on.
    resume_data = {
        "full_name": form_data["full_name"],
        "target_title": form_data["target_title"],
        "email": form_data["email"],
        "phone": form_data["phone"],
        "location": form_data["location"],
        "linkedin": form_data["linkedin"],
        "website": form_data["website"],
        "summary": summary,
        "experience": experience,
        "skills": skills,
        "education": education,
        "certifications": certifications,
    }
    request.session["resume_data"] = resume_data
    # A fresh generation starts a new record, not an edit of a previously saved one.
    request.session.pop("resume_id", None)

    return redirect("resume_edit")


# ---------------------------------------------------------------------------
# Step 3: Edit Resume page
# ---------------------------------------------------------------------------

def resume_edit(request):
    """Let the user tweak the AI-generated (or manually written) resume."""

    if request.method == "POST":
        resume_data = {
            "full_name": request.POST.get("full_name", "").strip(),
            "target_title": request.POST.get("target_title", "").strip(),
            "email": request.POST.get("email", "").strip(),
            "phone": request.POST.get("phone", "").strip(),
            "location": request.POST.get("location", "").strip(),
            "linkedin": request.POST.get("linkedin", "").strip(),
            "website": request.POST.get("website", "").strip(),
            "summary": request.POST.get("summary", "").strip(),
            "experience": _text_to_experience(request.POST.get("experience_text", "")),
            "skills": _skills_to_list(request.POST.get("skills_text", "")),
            "education": _lines_to_list(request.POST.get("education_text", "")),
            "certifications": _certs_to_list(request.POST.get("certifications_text", "")),
        }

        if not resume_data["full_name"]:
            messages.error(request, "Full name is required.")
            return render(request, "accounts/resume_builder/resume_edit.html", {"resume": resume_data})

        # Save edited resume: create or update the DB record.
        resume_id = request.session.get("resume_id")
        resume_obj = None
        if resume_id:
            resume_obj = Resume.objects.filter(pk=resume_id).first()
        if resume_obj is None:
            resume_obj = Resume()

        for field, value in resume_data.items():
            setattr(resume_obj, field, value)
        resume_obj.save()

        request.session["resume_id"] = resume_obj.pk
        request.session["resume_data"] = resume_data
        messages.success(request, "Resume Created Successfully!")
        return redirect("resume_preview")

    # GET: prefill from whatever is currently in the session.
    resume_data = request.session.get("resume_data")
    if not resume_data:
        messages.error(request, "Generate a resume first.")
        return redirect("resume_builder")

    # Flatten list/structured fields into editable text for the textareas.
    edit_context = dict(resume_data)
    edit_context["skills_text"] = _skills_to_text(resume_data.get("skills"))
    edit_context["education_text"] = _lines_to_text(resume_data.get("education"))
    edit_context["certifications_text"] = _lines_to_text(resume_data.get("certifications"))
    edit_context["experience_text"] = _experience_to_text(resume_data.get("experience"))

    return render(request, "accounts/resume_builder/resume_edit.html", {"resume": edit_context})


# ---------------------------------------------------------------------------
# Step 4: Resume preview (also used for Print)
# ---------------------------------------------------------------------------

def _load_current_resume(request):
    """Session first (fast path), falling back to the saved DB record."""
    resume_data = request.session.get("resume_data")
    if resume_data:
        return resume_data

    resume_id = request.session.get("resume_id")
    if resume_id:
        resume_obj = Resume.objects.filter(pk=resume_id).first()
        if resume_obj:
            return resume_obj.to_context()

    return None


def resume_preview(request):
    """Read-only preview of the current resume, with Edit / Print / Download actions."""
    resume_data = _load_current_resume(request)
    if not resume_data:
        messages.error(request, "No resume to preview yet. Generate one first.")
        return redirect("resume_builder")

    return render(request, "accounts/resume_builder/resume_preview.html", {
        "resume": resume_data,
        "resume_id": request.session.get("resume_id"),
    })


# ---------------------------------------------------------------------------
# Step 5: Download edited resume as PDF
# ---------------------------------------------------------------------------

def download_resume_pdf(request):
    resume_data = _load_current_resume(request)
    if not resume_data:
        return HttpResponse("No resume data found. Please fill the form first.", status=400)

    html_string = render_to_string("resume_builder/resume_pdf.html", {"resume": resume_data})
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri("/")).write_pdf()

    safe_name = (resume_data.get("full_name") or "resume").strip().replace(" ", "_")
    response = HttpResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{safe_name}_resume.pdf"'
    return response