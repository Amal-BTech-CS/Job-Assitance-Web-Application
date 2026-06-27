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


    skills = models.TextField(

        blank=True

    )


    resume = models.FileField(

        upload_to="resumes/",

        null=True,

        blank=True

    )


    extracted_data = models.JSONField(

        null=True,

        blank=True

    )



    def __str__(self):

        return self.full_name or self.user.username





# ==========================
# Education
# ==========================


class Education(models.Model):


    profile = models.ForeignKey(

        Profile,

        on_delete=models.CASCADE,

        related_name="education"

    )


    degree = models.CharField(

        max_length=200

    )


    college = models.CharField(

        max_length=200

    )


    percentage = models.CharField(

        max_length=50,

        blank=True

    )


    start_year = models.CharField(

        max_length=10

    )


    end_year = models.CharField(

        max_length=10

    )


    education_type = models.CharField(

        max_length=50,

        default="degree"

    )



    def __str__(self):

        return self.degree





# ==========================
# Experience
# ==========================


class Experience(models.Model):


    profile = models.ForeignKey(

        Profile,

        on_delete=models.CASCADE,

        related_name="experience"

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


    description = models.TextField(

        blank=True

    )



    def __str__(self):

        return self.job_title





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