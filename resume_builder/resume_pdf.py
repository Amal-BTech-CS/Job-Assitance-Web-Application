from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit

# Reuse the same cleaning logic as views.py instead of a separate,
# weaker comma-only split
from .views import _skills_to_list, _load_current_resume

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_LEFT = 54
MARGIN_RIGHT = 54
MARGIN_BOTTOM = 50
CONTENT_WIDTH = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT
PAGE_CENTER_X = PAGE_WIDTH / 2

BLACK = (0, 0, 0)


def download_resume_pdf(request):
    # Was: request.session.get("form_data")  <- raw, unedited intake data
    # Now: pulls the *edited* resume (session first, DB fallback) so PDF
    # matches whatever the user last saved on the Edit page.
    resume_data = _load_current_resume(request)

    if not resume_data:
        return HttpResponse("No resume data found.", status=400)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="Resume.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    y = [PAGE_HEIGHT - 54]

    def new_page():
        p.showPage()
        y[0] = PAGE_HEIGHT - 54

    def ensure_space(needed):
        if y[0] - needed < MARGIN_BOTTOM:
            new_page()

    def draw_centered(text, font="Helvetica", size=11, leading=16, gap_after=0):
        if not text or not text.strip():
            return
        p.setFont(font, size)
        p.setFillColorRGB(*BLACK)
        wrapped = simpleSplit(text, font, size, CONTENT_WIDTH)
        for line in wrapped:
            ensure_space(leading)
            p.drawCentredString(PAGE_CENTER_X, y[0], line)
            y[0] -= leading
        y[0] -= gap_after

    def draw_heading(text):
        ensure_space(28)
        p.setFillColorRGB(*BLACK)
        p.setFont("Helvetica-Bold", 12)
        p.drawString(MARGIN_LEFT, y[0], text.upper())
        y[0] -= 6
        p.setLineWidth(0.75)
        p.setStrokeColorRGB(*BLACK)
        p.line(MARGIN_LEFT, y[0], PAGE_WIDTH - MARGIN_RIGHT, y[0])
        y[0] -= 16

    def draw_paragraph(text, font="Helvetica", size=10.5, leading=14, indent=0, bullet=False):
        if not text or not text.strip():
            return
        p.setFont(font, size)
        p.setFillColorRGB(*BLACK)
        x = MARGIN_LEFT + indent
        max_width = CONTENT_WIDTH - indent

        for raw_line in text.split("\n"):
            raw_line = raw_line.strip()
            if not raw_line:
                y[0] -= leading * 0.5
                continue

            display = ("•  " + raw_line) if bullet else raw_line
            wrapped = simpleSplit(display, font, size, max_width)

            for wline in wrapped:
                ensure_space(leading)
                p.drawString(x, y[0], wline)
                y[0] -= leading

    def draw_skills_horizontal(skills_list, font="Helvetica", size=10.5, leading=14, separator="   |   "):
        if not skills_list:
            return
        text = separator.join(skills_list)
        p.setFont(font, size)
        p.setFillColorRGB(*BLACK)
        wrapped = simpleSplit(text, font, size, CONTENT_WIDTH)
        for wline in wrapped:
            ensure_space(leading)
            p.drawString(MARGIN_LEFT, y[0], wline)
            y[0] -= leading

    def draw_skills_vertical(skills_list, font="Helvetica", size=10.5, leading=14):
        if not skills_list:
            return
        for skill in skills_list:
            draw_paragraph(skill, font=font, size=size, leading=leading, bullet=True)

    def draw_experience_block(experience):
        """
        Now takes the already-structured experience list (from resume_data),
        not raw text — since resume_data.experience is
        [{"role_line": "...", "bullets": [...]}], not a blob of text.
        """
        if not experience:
            return

        for job in experience:
            title_line = job.get("role_line", "")
            bullet_lines = job.get("bullets", [])

            if title_line:
                wrapped_title = simpleSplit(title_line, "Helvetica-Bold", 11, CONTENT_WIDTH)
                p.setFont("Helvetica-Bold", 11)
                p.setFillColorRGB(*BLACK)
                for wline in wrapped_title:
                    ensure_space(15)
                    p.drawString(MARGIN_LEFT, y[0], wline)
                    y[0] -= 15
                y[0] -= 2

            for bl in bullet_lines:
                draw_paragraph(bl, bullet=True)

            y[0] -= 10

    # ----- Header: Name (centered) -----
    draw_centered(resume_data.get("full_name", ""), font="Helvetica-Bold", size=26, leading=30, gap_after=4)

    # ----- Target title / subtitle (centered) -----
    if resume_data.get("target_title"):
        draw_centered(resume_data.get("target_title", ""), font="Helvetica", size=13, leading=18, gap_after=2)

    # ----- Contact line (centered) -----
    contact_bits = [
        resume_data.get("location", ""),
        resume_data.get("email", ""),
        resume_data.get("phone", ""),
        resume_data.get("linkedin", ""),
        resume_data.get("website", ""),
    ]
    contact_line = "  |  ".join(bit for bit in contact_bits if bit)
    draw_centered(contact_line, font="Helvetica", size=9.5, leading=13, gap_after=10)

    p.setLineWidth(1)
    p.setStrokeColorRGB(*BLACK)
    p.line(MARGIN_LEFT, y[0], PAGE_WIDTH - MARGIN_RIGHT, y[0])
    y[0] -= 24

    # ----- Summary -----
    if resume_data.get("summary", "").strip():
        draw_heading("Professional Summary")
        draw_paragraph(resume_data.get("summary", ""))
        y[0] -= 10

    # ----- Skills -----
    # skills is already a clean list here (produced by _skills_to_list
    # earlier in the pipeline) — no re-splitting needed.
    skills_list = resume_data.get("skills", [])
    if skills_list:
        draw_heading("Skills")
        if len(skills_list) > 5:
            draw_skills_horizontal(skills_list)
        else:
            draw_skills_vertical(skills_list)
        y[0] -= 10

    # ----- Experience -----
    if resume_data.get("experience"):
        draw_heading("Work Experience")
        draw_experience_block(resume_data.get("experience"))

    # ----- Education -----
    education = resume_data.get("education", [])
    if education:
        draw_heading("Education")
        draw_paragraph("\n".join(education))
        y[0] -= 10

    # ----- Certifications -----
    certifications = resume_data.get("certifications", [])
    if certifications:
        draw_heading("Certifications")
        draw_paragraph("\n".join(certifications), bullet=True)

    p.save()
    return response