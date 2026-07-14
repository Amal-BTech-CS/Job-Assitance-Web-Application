from django.db import models


class Resume(models.Model):
    """A saved / editable resume record.

    The AI only ever polishes the summary + experience sections; everything
    else (contact info, skills, education, certifications) comes straight
    from the user. This model stores the *final* version of a resume after
    the user has reviewed and edited the AI-generated content, so it can be
    reloaded for preview, printing, or PDF download.
    """

    # Basic info
    full_name = models.CharField(max_length=150)
    target_title = models.CharField(max_length=150, blank=True)
    email = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=150, blank=True)
    linkedin = models.CharField(max_length=200, blank=True)
    website = models.CharField(max_length=200, blank=True)

    # AI-assisted content (editable afterwards)
    summary = models.TextField(blank=True)

    # Structured content stored as JSON so it round-trips cleanly between
    # the DB, the edit form, the preview page, and the PDF exporter.
    # skills: ["Python", "Django", ...]
    skills = models.JSONField(default=list, blank=True)
    # experience: [{"role_line": "...", "bullets": ["...", "..."]}, ...]
    experience = models.JSONField(default=list, blank=True)
    # education: ["B.Tech in CS, Anna University, 2016 - 2020", ...]
    education = models.JSONField(default=list, blank=True)
    # certifications: ["AWS Certified Solutions Architect", ...]
    certifications = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.full_name} — {self.target_title or 'Resume'} ({self.pk})"

    def to_context(self):
        """Flat dict used by the preview/edit templates and the PDF export."""
        return {
            "id": self.pk,
            "full_name": self.full_name,
            "target_title": self.target_title,
            "email": self.email,
            "phone": self.phone,
            "location": self.location,
            "linkedin": self.linkedin,
            "website": self.website,
            "summary": self.summary,
            "skills": self.skills,
            "experience": self.experience,
            "education": self.education,
            "certifications": self.certifications,
        }
