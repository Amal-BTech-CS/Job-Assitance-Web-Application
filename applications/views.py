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
from django.views.decorators.http import require_POST
from accounts.ai.email_notify import send_status_email
from accounts.ai.ats import ats_score, extract_pdf_text
from accounts.ai.cover import generate_cover_letter

@login_required
def apply_job(request, job_id):

    profile = get_object_or_404(Profile, user=request.user)
    job = get_object_or_404(Job, id=job_id)

    # Prevent duplicate applications
    if Application.objects.filter(
        applicant=profile,
        job=job
    ).exists():
        messages.warning(request, "You already applied for this job.")
        return redirect("jobseeker_dashboard")

    if request.method == "POST":

        form = ApplicationForm(request.POST, request.FILES)
        action = request.POST.get("action")

        if form.is_valid():

            resume_option = form.cleaned_data.get("resume_option")
            new_resume = request.FILES.get("new_resume")

            resume_file = None
            cover_letter = ""

            # ==========================================
            # GENERATE COVER LETTER PREVIEW ONLY
            # ==========================================
            if action == "generate":

                if resume_option == "profile":

                    latest_resume = Resume.objects.filter(
                        profile=profile
                    ).order_by("-id").first()

                    if not latest_resume:
                        messages.error(request, "No profile resume found.")
                        return redirect("jobseeker_profile")

                    # Same pattern as upload_resume(): open the FieldFile
                    # explicitly (works for S3), read, then close.
                    latest_resume.resume_file.open("rb")
                    cover_letter = generate_cover_letter(
                        latest_resume.resume_file,
                        job.title,
                        job.company.company_name
                    )
                    latest_resume.resume_file.close()

                elif resume_option == "new":

                    if not new_resume:
                        messages.error(request, "Please upload a resume.")
                        return redirect("apply_job", job_id=job.id)

                    # Freshly uploaded file - already a readable in-memory
                    # file object, no storage-level open() needed.
                    cover_letter = generate_cover_letter(
                        new_resume,
                        job.title,
                        job.company.company_name
                    )
                    new_resume.seek(0)  # rewind so it can still be saved later

                return render(
                    request,
                    "accounts/apply_job.html",
                    {
                        "form": form,
                        "job": job,
                        "cover_letter": cover_letter,
                    }
                )

            # ==========================================
            # CASE 1 : USE PROFILE RESUME
            # ==========================================
            if resume_option == "profile":

                latest_resume = Resume.objects.filter(
                    profile=profile
                ).order_by("-id").first()

                if not latest_resume:
                    messages.error(request, "No profile resume found.")
                    return redirect("jobseeker_profile")

                resume_file = latest_resume.resume_file

                # Generate AI Cover Letter (same open/close pattern as above)
                resume_file.open("rb")
                cover_letter = generate_cover_letter(
                    resume_file,
                    job.title,
                    job.company.company_name
                )
                resume_file.close()

            # ==========================================
            # CASE 2 : UPLOAD NEW RESUME
            # ==========================================
            elif resume_option == "new":

                if not new_resume:
                    messages.error(request, "Please upload a resume.")
                    return redirect("apply_job", job_id=job.id)

                cover_letter = generate_cover_letter(
                    new_resume,
                    job.title,
                    job.company.company_name
                )
                new_resume.seek(0)  # rewind so the full file saves below

                resume_file = new_resume

            # ==========================================
            # INVALID OPTION
            # ==========================================
            else:

                messages.error(
                    request,
                    "Invalid resume option."
                )

                return redirect(
                    "apply_job",
                    job_id=job.id
                )
             # ==========================================
            # CALCULATE ATS SCORE
            # Reuses the same ats.py logic as your ATS Calculator page,
            # matching the resume against this job's description + skills.
            # ==========================================
            calculated_ats_score = None

            try:
                if resume_option == "profile":
                    resume_file.open("rb")
                    resume_text_for_ats = extract_pdf_text(resume_file)
                    resume_file.close()
                else:
                    new_resume.seek(0)
                    resume_text_for_ats = extract_pdf_text(new_resume)
                    new_resume.seek(0)  # rewind so it can still be saved below

                job_text_for_ats = f"{job.description}\n{job.job_skills}"

                ats_result = ats_score(resume_text_for_ats, job_text_for_ats)
                calculated_ats_score = ats_result["final"]

            except Exception:
                # Never block a submission just because scoring failed
                calculated_ats_score = None
            # ==========================================
            # SAVE APPLICATION
            # ==========================================
            cover_letter = request.POST.get("cover_letter") or cover_letter
            Application.objects.create(
                applicant=profile,
                job=job,
                resume_file=resume_file,
                cover_letter=cover_letter,
                status="applied",
                ats_score=calculated_ats_score
            )

            messages.success(
                request,
                "Application submitted successfully!"
            )

            return redirect("my_applications")

        else:

            messages.error(
                request,
                "Invalid form submission."
            )

    else:

        form = ApplicationForm()

    return render(
        request,
        "accounts/apply_job.html",
        {
            "form": form,
            "job": job,
            "cover_letter": "",
        }
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

    # ==========================================
    # SCREENING FILTER: only show strong ATS matches
    # ?filter=qualified in the URL switches the view
    # ==========================================
    show_qualified_only = request.GET.get("filter") == "qualified"

    if show_qualified_only:
        applications = applications.filter(
            ats_score__gte=60
        ).order_by("-ats_score")

    qualified_count = job.applications.filter(ats_score__gte=60).count()

    return render(request, "accounts/job_applicants.html", {
        "job": job,
        "applications": applications,
        "show_qualified_only": show_qualified_only,
        "qualified_count": qualified_count,
    })



@login_required
def applicant_detail(request, application_id):

    company = get_object_or_404(CompanyProfile, user=request.user)

    application = get_object_or_404(
        Application,
        id=application_id,
        job__company=company
    )

    # ==========================
    # AUTO-MARK AS "VIEWED"
    # ==========================
    if application.status in ("applied", "under_review"):
        application.status = "viewed"
        application.save(update_fields=["status", "updated_at"])

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
@login_required
def application_detail(request, application_id):

    profile = get_object_or_404(Profile, user=request.user)

    application = get_object_or_404(
        Application,
        id=application_id,
        applicant=profile
    )

    return render(request, "accounts/application_detail.html", {
        "application": application,
    })
@login_required
@require_POST
def update_application_status(request, application_id):
    """
    Employer-side action to move an application through the pipeline
    (shortlist / interview / hire / reject). The candidate instantly
    sees the new status on their My Applications / Application Detail
    pages since both sides read the same Application.status field.
    """

    company = get_object_or_404(CompanyProfile, user=request.user)

    application = get_object_or_404(
        Application,
        id=application_id,
        job__company=company
    )

    new_status = request.POST.get("status")

    valid_statuses = dict(Application.APPLICATION_STATUS)

    if new_status not in valid_statuses:
        messages.error(request, "Invalid status.")
        return redirect("applicant_detail", application_id=application.id)

    application.status = new_status
    application.save(update_fields=["status", "updated_at"])
    send_status_email(application)

    messages.success(
        request,
        f"Application marked as {valid_statuses[new_status]}."
    )

    next_url = request.POST.get("next")
    if next_url:
        return redirect(next_url)

    return redirect("applicant_detail", application_id=application.id)


from django.db.models import Q
