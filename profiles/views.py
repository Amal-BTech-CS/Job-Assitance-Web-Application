from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache

from accounts.models import (
    Profile,
    Resume,
    Education,
    Experience,
    Skill,
    Project,
    CompanyProfile,
)
from accounts.ai.resume_parser import (
    extract_resume_text,
    analyze_resume
)


@never_cache
@login_required
def jobseeker_profile(request):

    if request.user.is_staff or request.user.is_superuser:
        return redirect("admin:index")

    profile, created = Profile.objects.get_or_create(
        user=request.user
    )

    # -----------------------------------
    # Load Resume Related Data
    # -----------------------------------

    resume = Resume.objects.filter(
        profile=profile
    ).first()

    education = None
    experience = []
    skills = []
    projects = []

    if resume:
        education = Education.objects.filter(
            resume=resume
        ).first()

        experience = Experience.objects.filter(
            resume=resume
        )

        skills = Skill.objects.filter(
            resume=resume
        )

        projects = Project.objects.filter(
            resume=resume
        )

    # -----------------------------------
    # POST
    # -----------------------------------

    if request.method == "POST":

        # ==========================================
        # SAVE PROFILE
        # ==========================================

        if "save_profile" in request.POST:

            profile.full_name = request.POST.get("full_name", "")
            profile.email = request.POST.get("email", "")
            profile.phone = request.POST.get("phone", "")
            profile.linkedin = request.POST.get("linkedin", "")
            profile.github = request.POST.get("github", "")

            profile.save()

            return redirect("profile_view")

        # ==========================================
        # ADD EXPERIENCE
        # ==========================================

        elif "add_experience" in request.POST:

            if resume:

                Experience.objects.create(
                    resume=resume,
                    job_title=request.POST.get("job_title", ""),
                    company=request.POST.get("company", ""),
                    start_date=request.POST.get("start_date", ""),
                    end_date=request.POST.get("end_date", "")
                )

            return redirect("jobseeker_profile")

        # ==========================================
        # DELETE EXPERIENCE
        # ==========================================

        elif "delete_experience" in request.POST:

            exp_id = request.POST.get("experience_id")

            if resume:
                Experience.objects.filter(
                    id=exp_id,
                    resume=resume
                ).delete()

            return redirect("jobseeker_profile")

        # ==========================================
        # UPLOAD RESUME
        # ==========================================
        elif "update_education" in request.POST:

            if resume:

                edu, created = Education.objects.get_or_create(
                    resume=resume
                )
                edu.qualification_level = request.POST.get("qualification_level", "")
                edu.degree = request.POST.get("degree", "")
                edu.college = request.POST.get("college", "")
                edu.start_year = request.POST.get("start_year", "")
                edu.end_year = request.POST.get("end_year", "")

                cgpa = request.POST.get("cgpa", "").strip()

                edu.cgpa = cgpa if cgpa else ""

                edu.save()

        elif "upload_resume" in request.POST:

            uploaded_resume = request.FILES.get("resume")

            if uploaded_resume:

                resume, created = Resume.objects.get_or_create(
                    profile=profile
                )

                if resume.resume_file:
                    resume.resume_file.delete(save=False)

                resume.resume_file = uploaded_resume
                resume.save()

                resume.resume_file.open("rb")

                text = extract_resume_text(
                    resume.resume_file
                )

                resume.resume_file.close()
                # AI Parsing
                data = analyze_resume(text)
                personal = data.get("personal_information", {})

                profile.full_name = personal.get("name", "")
                profile.email = personal.get("email", "")
                profile.phone = personal.get("phone", "")
                profile.linkedin = personal.get("linkedin", "")
                profile.github = personal.get("github", "")
                profile.summary = data.get("summary", "")

                profile.save()
                # -----------------------------------
                # Skills
                # -----------------------------------

                Skill.objects.filter(
                    resume=resume
                ).delete()

                skills_data = data.get("skills", [])

                if isinstance(skills_data, list):

                    for skill in skills_data:

                        if isinstance(skill, dict):

                            Skill.objects.create(
                                resume=resume,
                                skill_name=skill.get("skill_name", "")
                            )

                        else:

                            Skill.objects.create(
                                resume=resume,
                                skill_name=skill
                            )
                # -----------------------------------
                # Education
                # -----------------------------------

                Education.objects.filter(
                    resume=resume
                ).delete()

                edu = data.get("education", {})

                if edu:

                    Education.objects.create(
                        resume=resume,
                        qualification_level=edu.get("qualification_level", ""),
                        degree=edu.get("degree", ""),
                        college=edu.get("college", ""),
                        cgpa=edu.get("cgpa", ""),
                        start_year=edu.get("start_year", ""),
                        end_year=edu.get("end_year", "")
                    )

                # -----------------------------------
                # Experience
                # -----------------------------------

                Experience.objects.filter(
                    resume=resume
                ).delete()

                for exp in data.get("experience", []):

                    Experience.objects.create(
                        resume=resume,
                        job_title=exp.get("job_title", ""),
                        company=exp.get("company", ""),
                        start_date=exp.get("start_date", ""),
                        end_date=exp.get("end_date", "")
                    )
                # ==========================
                # PROJECTS
                # ==========================

                Project.objects.filter(
                    resume=resume
                ).delete()

                projects = data.get("projects", [])

                for project in projects:

                    Project.objects.create(
                        resume=resume,
                        title=project.get("title", ""),
                        description=project.get("description", ""),
                        technologies=project.get("technologies", ""),
                        github_link=project.get("github_link", "")
                    )

                return redirect("jobseeker_profile")

    return render(
        request,
        "accounts/jobseeker_profile.html",
        {
            "profile": profile,
            "resume": resume,
            "education": education,
            "experience": experience,
            "skills": skills,
            "projects": projects,
        }
    )


@login_required
@never_cache
def profile_view(request):

    profile = Profile.objects.get(
        user=request.user
    )

    resume = Resume.objects.filter(
        profile=profile
    ).first()

    education = None
    experience = []
    skills = []
    projects = []

    if resume:
        education = Education.objects.filter(
            resume=resume
        ).first()

        experience = Experience.objects.filter(
            resume=resume
        )

        skills = Skill.objects.filter(
            resume=resume
        )

        projects = Project.objects.filter(
            resume=resume
        )

    return render(
        request,
        "accounts/profile_view.html",
        {
            "profile": profile,
            "education": education,
            "experience": experience,
            "skills": skills,
            "projects": projects,
        }
    )


@login_required
@never_cache
def company_profile(request):

    profile, created = CompanyProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":

        profile.company_name = request.POST.get(
            "company_name"
        )

        profile.company_email = request.POST.get(
            "company_email"
        )

        profile.company_phone = request.POST.get(
            "company_phone"
        )

        profile.website = request.POST.get(
            "website"
        )

        profile.description = request.POST.get(
            "description"
        )

        profile.save()

        return redirect(
            "company_profile_view"
        )

    return render(

        request,

        "accounts/company_profile.html",

        {
            "profile": profile
        }

    )


@login_required
@never_cache
def company_profile_view(request):

    profile = CompanyProfile.objects.get(
        user=request.user
    )

    return render(

        request,

        "accounts/company_profile_view.html",

        {
            "profile": profile
        }

    )
