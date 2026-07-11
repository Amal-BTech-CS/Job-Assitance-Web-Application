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
        messages.warning(request, "You have already applied for this job.")
        return redirect("jobseeker_dashboard")

    if request.method == "POST":

        form = ApplicationForm(request.POST, request.FILES)

        if form.is_valid():

            resume_option = form.cleaned_data["resume_option"]
            cover_letter = form.cleaned_data["cover_letter"]
            new_resume = form.cleaned_data.get("new_resume")

            resume_file = None

            # ====================================
            # USE PROFILE RESUME
            # ====================================
            if resume_option == "profile":

                latest_resume = Resume.objects.filter(
                    profile=profile
                ).first()

                if not latest_resume or not latest_resume.resume_file:
                    messages.error(
                        request,
                        "Please upload a resume in your profile first."
                    )

                    return redirect("jobseeker_profile")

                # Read profile resume
                latest_resume.resume_file.open("rb")
                resume_content = latest_resume.resume_file.read()
                latest_resume.resume_file.close()

                extension = os.path.splitext(
                    latest_resume.resume_file.name
                )[1]

                filename = (
                    f"application_resumes/"
                    f"{uuid.uuid4()}{extension}"
                )

                saved_path = default_storage.save(
                    filename,
                    ContentFile(resume_content)
                )

                resume_file = saved_path

            # ====================================
            # USE NEWLY UPLOADED RESUME
            # ====================================
            elif resume_option == "new":

                extension = os.path.splitext(
                    new_resume.name
                )[1]

                filename = (
                    f"application_resumes/"
                    f"{uuid.uuid4()}{extension}"
                )

                saved_path = default_storage.save(
                    filename,
                    new_resume
                )

                resume_file = saved_path

            else:

                form.add_error(
                    "resume_option",
                    "Invalid resume option."
                )

                return render(
                    request,
                    "accounts/apply_job.html",
                    {
                        "form": form,
                        "job": job,
                    }
                )

            # ====================================
            # CREATE APPLICATION
            # ====================================

            Application.objects.create(
                applicant=profile,
                job=job,
                resume_file=resume_file,
                cover_letter=cover_letter,
                status="applied",
            )

            messages.success(
                request,
                "Application submitted successfully!"
            )

            return redirect("my_applications")

        # Form validation failed
        print(form.errors)

    else:

        form = ApplicationForm()

    return render(
        request,
        "accounts/apply_job.html",
        {
            "form": form,
            "job": job,
        },
    )

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
