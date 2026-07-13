from django.contrib.auth.models import AbstractUser
from django.db import models



# ==========================
# Custom User
# ==========================


class User(AbstractUser):

    USER_TYPES = (

        ('jobseeker', 'Job Seeker'),

        ('company', 'Job Provider'),

    )


    user_type = models.CharField(

        max_length=20,

        choices=USER_TYPES,

        default='jobseeker'

    )


    def __str__(self):

        return self.username





# ==========================
# Job Seeker Profile
# ==========================


class Profile(models.Model):


    user = models.OneToOneField(

        User,

        on_delete=models.CASCADE,

        related_name="profile"

    )


    full_name = models.CharField(

        max_length=200,

        blank=True

    )


    email = models.EmailField(

        blank=True

    )


    phone = models.CharField(

        max_length=15,

        blank=True

    )


    linkedin = models.URLField(

        blank=True

    )


    github = models.URLField(

        blank=True

    )


    summary = models.TextField(

        blank=True

    )


    def __str__(self):

        return self.full_name or self.user.username


class Resume(models.Model):

    profile = models.OneToOneField(
        Profile,
        on_delete=models.CASCADE,
        related_name="resume"
    )

    resume_file = models.FileField(
        upload_to="profile_resumes/",
        null=True,
        blank=True
    )

    extracted_data = models.JSONField(
        null=True,
        blank=True
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )
    def __str__(self):
        return f"Resume - {self.profile.full_name}"

# ==========================
# Education
# ==========================

class Education(models.Model):

    resume = models.ForeignKey(
    Resume,
    on_delete=models.CASCADE,
    related_name="educations"
)
    qualification_level=models.CharField(
        max_length=200,
        blank=True
    )
    degree = models.CharField(
        max_length=200
    )


    college = models.CharField(
        max_length=200
    )


    cgpa = models.CharField(max_length=50, blank=True, null=True)

    start_year = models.CharField(
        max_length=10,
        blank=True
    )


    end_year = models.CharField(
        max_length=10,
        blank=True
    )


    def __str__(self):

        return self.degree

class Skill(models.Model):

    resume = models.ForeignKey(
        Resume,
        on_delete=models.CASCADE,
        related_name="skills"
    )

    skill_name = models.CharField(max_length=100)
    def __str__(self):
        return self.skill_name
class Experience(models.Model):


    resume = models.ForeignKey(
    Resume,
    on_delete=models.CASCADE,
    related_name="experiences"
    )


    job_title = models.CharField(
        max_length=200
    )


    company = models.CharField(
        max_length=200
    )


    start_date = models.CharField(
        max_length=50
    )


    end_date = models.CharField(
        max_length=50,
        blank=True
    )


    def __str__(self):

        return self.job_title

class Project(models.Model):

    resume = models.ForeignKey(
        Resume,
        on_delete=models.CASCADE,
        related_name="projects"
    )

    title = models.CharField(
        max_length=200
    )

    description = models.TextField(
        blank=True
    )

    technologies = models.TextField(
        blank=True
    )

    github_link = models.URLField(
        blank=True
    )

    def __str__(self):
        return self.title
# ==========================
# Company Profile
# ==========================


class CompanyProfile(models.Model):


    user = models.OneToOneField(

        User,

        on_delete=models.CASCADE,

        related_name="company_profile"

    )


    company_name = models.CharField(

        max_length=200

    )


    company_email = models.EmailField()



    company_phone = models.CharField(

        max_length=15,

        blank=True

    )


    website = models.URLField(

        blank=True

    )


    description = models.TextField(

        blank=True

    )



    def __str__(self):

        return self.company_name
    
class Job(models.Model):

    JOB_STATUS = (
        ("Open", "Open"),
        ("Closed", "Closed"),
    )

    company = models.ForeignKey(
        CompanyProfile,
        on_delete=models.CASCADE,
        related_name="jobs"
    )

    title = models.CharField(
        max_length=200
    )

    location = models.CharField(
        max_length=150
    )

    employment_type = models.CharField(
        max_length=50
    )

    experience = models.CharField(
        max_length=100
    )

    salary = models.CharField(
        max_length=100
    )

    job_skills = models.TextField()

    description = models.TextField()

    status = models.CharField(
        max_length=10,
        choices=JOB_STATUS,
        default="Open"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.title} - {self.company.company_name}"

class Application(models.Model):

    APPLICATION_STATUS = (
        ("applied", "Applied"),
        ("under_review", "Under Review"),
        ("shortlisted", "Shortlisted"),
        ("interview", "Interview"),
        ("rejected", "Rejected"),
        ("hired", "Hired"),
    )

    # ==========================
    # RELATIONS
    # ==========================

    applicant = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="applications"
    )

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="applications"
    )

    # ==========================
    # RESUME USED FOR THIS APPLICATION
    # (Profile resume OR Newly Uploaded Resume)
    # ==========================

    resume_file = models.FileField(
        upload_to="application_resumes/",
        blank=True,
        null=True
    )

    # ==========================
    # COVER LETTER
    # ==========================

    cover_letter = models.TextField(
        blank=True
    )

    # ==========================
    # AI MATCH SCORE
    # ==========================

    ats_score = models.FloatField(
        null=True,
        blank=True
    )

    # ==========================
    # APPLICATION STATUS
    # ==========================

    status = models.CharField(
        max_length=20,
        choices=APPLICATION_STATUS,
        default="applied"
    )

    # ==========================
    # TIMESTAMPS
    # ==========================

    applied_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-applied_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["applicant", "job"],
                name="unique_job_application"
            )
        ]

    def __str__(self):
        return f"{self.applicant.full_name or self.applicant.user.username} → {self.job.title}"