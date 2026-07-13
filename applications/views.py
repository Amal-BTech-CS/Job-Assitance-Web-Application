from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import os
import uuid
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from accounts.models import (
    Profile,
    Resume,
    Education,
    Experience,
    Skill,
    Project,
    CompanyProfile,
    Job,
    Application,
)
from accounts.forms import ApplicationForm


@login_required
def apply_job(request, job_id):

    profile = get_object_or_404(Profile, user=request.user)
    job = get_object_or_404(Job, id=job_id)

    # Prevent duplicate applications
    if Application.objects.filter(applicant=profile, job=job).exists():
        messages.warning(request, "You already applied for this job.")
        return redirect("jobseeker_dashboard")

    if request.method == "POST":

        form = ApplicationForm(request.POST, request.FILES)

        if form.is_valid():

            resume_option = form.cleaned_data.get("resume_option")
            cover_letter = form.cleaned_data.get("cover_letter", "")
            new_resume = request.FILES.get("new_resume")  # SAFE

            resume_file = None

            # ==========================
            # CASE 1: PROFILE RESUME
            # ==========================
            if resume_option == "profile":
                latest_resume = Resume.objects.filter(profile=profile).first()

                if not latest_resume or not latest_resume.resume_file:
                    messages.error(request, "No profile resume found.")
                    return redirect("jobseeker_profile")

                # Read the profile resume
                latest_resume.resume_file.open("rb")
                resume_content = latest_resume.resume_file.read()
                latest_resume.resume_file.close()

                # Get original extension
                extension = os.path.splitext(latest_resume.resume_file.name)[1]

                # Create unique filename
                new_filename = f"application_resumes/{uuid.uuid4()}{extension}"

                # Save a copy to S3
                saved_path = default_storage.save(
                    new_filename,
                    ContentFile(resume_content)
                )

                resume_file = saved_path

            # ==========================
            # CASE 2: NEW RESUME
            # ==========================
            elif resume_option == "new":

                if not new_resume:
                    messages.error(request, "Please upload a resume.")
                    return redirect("apply_job", job_id=job.id)

                extension = os.path.splitext(new_resume.name)[1]

                new_filename = f"application_resumes/{uuid.uuid4()}{extension}"

                saved_path = default_storage.save(
                    new_filename,
                    new_resume
                )

                resume_file = saved_path

            else:
                messages.error(request, "Invalid resume option.")
                return redirect("apply_job", job_id=job.id)

            # ==========================
            # CREATE APPLICATION
            # ==========================
            Application.objects.create(
                applicant=profile,
                job=job,
                resume_file=resume_file,
                cover_letter=cover_letter,
                status="applied"
            )

            messages.success(request, "Application submitted successfully!")
            return redirect("my_applications")

        else:
            messages.error(request, "Invalid form submission.")

    else:
        form = ApplicationForm()

    return render(request, "accounts/apply_job.html", {
        "form": form,
        "job": job
    })


@login_required
def my_applications(request):

    profile = Profile.objects.get(user=request.user)

    applications = Application.objects.filter(applicant=profile).select_related("job")
    return render(request, "accounts/my_applications.html", {
        "applications": applications
    })


@login_required
def job_applicants(request, job_id):

    company = CompanyProfile.objects.get(user=request.user)

    job = get_object_or_404(Job, id=job_id, company=company)

    applications = job.applications.select_related("applicant").all()

    return render(request, "accounts/job_applicants.html", {
        "job": job,
        "applications": applications
    })


@login_required
def applicant_detail(request, application_id):

    application = get_object_or_404(
        Application,
        id=application_id
    )

    profile = application.applicant
    resume = Resume.objects.filter(profile=profile).first()

    education = None
    experience = []
    skills = []
    projects = []

    if resume:
        education = Education.objects.filter(resume=resume).first()
        experience = Experience.objects.filter(resume=resume)
        skills = Skill.objects.filter(resume=resume)
        projects = Project.objects.filter(resume=resume)

    return render(request, "accounts/applicant_detail.html", {
        "application": application,
        "profile": profile,
        "resume": resume,
        "education": education,
        "experience": experience,
        "skills": skills,
        "projects": projects,
    })
