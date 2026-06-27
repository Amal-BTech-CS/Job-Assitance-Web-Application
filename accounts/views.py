from django.shortcuts import render, redirect
from .forms import JobSeekerRegisterForm, CompanyRegisterForm
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from .ai.resume_parser import extract_resume_text
from .models import Profile, Education, Experience, CompanyProfile
from django.views.decorators.cache import never_cache
@login_required
@never_cache
def jobseeker_dashboard(request):
    return render(
        request,
        'accounts/jobseeker_dashboard.html'
    )


@login_required
@never_cache
def company_dashboard(request):
    return render(
        request,
        'accounts/company_dashboard.html'
    )



def jobseeker_register(request):

    if request.method == "POST":

        form = JobSeekerRegisterForm(request.POST)

        if form.is_valid():

            user = form.save(commit=False)

            user.user_type = "jobseeker"

            user.set_password(
                form.cleaned_data["password"]
            )

            user.save()


            Profile.objects.create(

                user=user

            )


            return redirect(
                "jobseeker_login"
            )


    else:

        form = JobSeekerRegisterForm()


    return render(

        request,

        "accounts/jobseeker_register.html",

        {
            "form": form
        }

    )
def company_register(request):

    if request.method == "POST":

        form = CompanyRegisterForm(request.POST)


        if form.is_valid():

            user = form.save(commit=False)


            user.user_type = "company"


            user.set_password(
                form.cleaned_data["password"]
            )


            user.save()



            CompanyProfile.objects.create(

                user=user,

                company_name=user.username,

                company_email=user.email

            )



            return redirect(

                "company_login"

            )



    else:

        form = CompanyRegisterForm()



    return render(

        request,

        "accounts/company_register.html",

        {

            "form": form

        }

    )

from django.contrib.auth import authenticate
from django.contrib.auth import login


from django.contrib.auth import authenticate, login


def jobseeker_login(request):

    error = None


    if request.method == "POST":


        username = request.POST.get(
            "username"
        )


        password = request.POST.get(
            "password"
        )



        user = authenticate(

            request,

            username=username,

            password=password

        )
        print(user, user.user_type if user else "No user")

        if user and user.user_type == "jobseeker":

            login(
                request,
                user
            )

            return redirect(
                "jobseeker_profile"
            )


        else:


            error = "Invalid Job Seeker credentials"



    return render(

        request,

        "accounts/jobseeker_login.html",

        {

            "error": error

        }

    )

def company_login(request):

    error = None


    if request.method == "POST":


        username = request.POST.get(
            "username"
        )


        password = request.POST.get(
            "password"
        )



        user = authenticate(

            request,

            username=username,

            password=password

        )



        if user and user.user_type == "company":

            login(
                request,
                user
            )

            return redirect(
                "company_profile"
            )


        else:


            error = "Invalid Company credentials"



    return render(

        request,

        "accounts/company_login.html",

        {

            "error": error

        }

    )

def home(request):

    if request.user.is_authenticated:

        if request.user.user_type == "jobseeker":

            return redirect(
                "jobseeker_dashboard"
            )

        elif request.user.user_type == "company":

            return redirect(
                "company_dashboard"
            )

    return render(
        request,
        "accounts/home.html"
    )
from django.contrib.auth import logout

def user_logout(request):
    logout(request)
    return redirect('home')

from django.shortcuts import render, redirect
from .models import Profile
from .models import Education, Experience
from .ai.resume_parser import (
    extract_resume_text,
    analyze_resume
)
@login_required
@never_cache
def jobseeker_profile(request):

    profile, created = Profile.objects.get_or_create(
    user=request.user
    )

    if request.method == "POST":

        # =========================
        # SAVE PROFILE
        # =========================

        if "save_profile" in request.POST:

            profile.full_name = request.POST.get(
                "full_name",
                ""
            )

            profile.email = request.POST.get(
                "email",
                ""
            )

            profile.phone = request.POST.get(
                "phone",
                ""
            )

            profile.linkedin = request.POST.get(
                "linkedin",
                ""
            )

            profile.github = request.POST.get(
                "github",
                ""
            )

            profile.summary = request.POST.get(
                "summary",
                ""
            )

            profile.skills = request.POST.get(
                "skills",
                ""
            )

            profile.save()

            return redirect(
                "profile_view"
            )



        # =========================
        # SAVE EDUCATION
        # =========================

        elif "save_education" in request.POST:

            education_levels = [
                "10th",
                "plus_two",
                "degree"
            ]

            for level in education_levels:

                degree = request.POST.get(
                    f"{level}_degree",
                    ""
                )

                college = request.POST.get(
                    f"{level}_college",
                    ""
                )

                percentage = request.POST.get(
                    f"{level}_percentage",
                    ""
                )

                start_year = request.POST.get(
                    f"{level}_start_year",
                    ""
                )

                end_year = request.POST.get(
                    f"{level}_end_year",
                    ""
                )

                if (
                    degree.strip()
                    or college.strip()
                    or percentage.strip()
                ):

                    Education.objects.update_or_create(

                        profile=profile,

                        education_type=level,

                        defaults={

                            "degree": degree,

                            "college": college,

                            "percentage": percentage,

                            "start_year": start_year,

                            "end_year": end_year

                        }

                    )

            return redirect(
                "jobseeker_profile"
            )



        # =========================
        # ADD EXPERIENCE
        # =========================

        elif "add_experience" in request.POST:

            job_title = request.POST.get(
                "job_title",
                ""
            )

            company = request.POST.get(
                "company",
                ""
            )

            description = request.POST.get(
                "description",
                ""
            )

            if (
                job_title.strip()
                or company.strip()
                or description.strip()
            ):

                Experience.objects.create(

                    profile=profile,

                    job_title=job_title,

                    company=company,

                    start_date=request.POST.get(
                        "start_date",
                        ""
                    ),

                    end_date=request.POST.get(
                        "end_date",
                        ""
                    ),

                    description=description

                )

            return redirect(
                "jobseeker_profile"
            )



        # =========================
        # RESUME UPLOAD
        # =========================

        # =========================
        # RESUME UPLOAD
        # =========================


        # =========================
        # RESUME UPLOAD
        # =========================

        elif "upload_resume" in request.POST:

            resume = request.FILES.get("resume")

            if resume:

                profile.resume = resume
                profile.save()

                text = extract_resume_text(
                    profile.resume.path
                )

                data = analyze_resume(text)

                profile.extracted_data = data

                profile.full_name = data.get(
                    "name",
                    ""
                )

                profile.email = data.get(
                    "email",
                    ""
                )

                profile.phone = data.get(
                    "phone",
                    ""
                )

                profile.linkedin = data.get(
                    "linkedin",
                    ""
                )

                profile.github = data.get(
                    "github",
                    ""
                )

                profile.summary = data.get(
                    "summary",
                    ""
                )

                profile.save()

                # =========================
                # EDUCATION
                # =========================

                Education.objects.filter(
                    profile=profile
                ).delete()

                education_data = data.get(
                    "education",
                    []
                )

                if isinstance(
                    education_data,
                    dict
                ):
                    education_data = [
                        education_data
                    ]

                for edu in education_data:

                    degree = edu.get(
                        "degree",
                        ""
                    )

                    college = edu.get(
                        "college",
                        ""
                    )

                    percentage = edu.get(
                        "percentage",
                        edu.get(
                            "cgpa",
                            ""
                        )
                    )

                    start_year = edu.get(
                        "start_year",
                        ""
                    )

                    end_year = edu.get(
                        "end_year",
                        ""
                    )

                    education_type = edu.get(
                        "education_type",
                        "degree"
                    )

                    if not degree:

                        text_check = (
                            college.lower()
                            if college
                            else ""
                        )

                    else:

                        text_check = degree.lower()

                    if (
                        "10th" in text_check
                        or "10 th" in text_check
                        or "sslc" in text_check
                        or "secondary" in text_check
                    ):

                        education_type = "10th"

                    elif (
                        "12th" in text_check
                        or "12 th" in text_check
                        or "plus two" in text_check
                        or "higher secondary" in text_check
                    ):

                        education_type = "plus_two"

                    else:

                        education_type = "degree"

                    Education.objects.update_or_create(

                        profile=profile,

                        education_type=education_type,

                        defaults={

                            "degree": degree,

                            "college": college,

                            "percentage": percentage,

                            "start_year": start_year,

                            "end_year": end_year

                        }

                    )

                # =========================
                # EXPERIENCE
                # =========================

                Experience.objects.filter(
                    profile=profile
                ).delete()

                experience_data = data.get(
                    "experience",
                    []
                )

                if isinstance(
                    experience_data,
                    dict
                ):
                    experience_data = [
                        experience_data
                    ]

                for exp in experience_data:

                    Experience.objects.create(

                        profile=profile,

                        job_title=exp.get(
                            "job_title",
                            ""
                        ),

                        company=exp.get(
                            "company",
                            ""
                        ),

                        start_date=exp.get(
                            "start_date",
                            ""
                        ),

                        end_date=exp.get(
                            "end_date",
                            ""
                        ),

                        description=exp.get(
                            "description",
                            ""
                        )

                    )

                # =========================
                # SKILLS
                # =========================

                skills = data.get(
                    "skills",
                    {}
                )

                all_skills = []

                if isinstance(
                    skills,
                    dict
                ):

                    for skill_list in skills.values():

                        all_skills.extend(
                            skill_list
                        )

                elif isinstance(
                    skills,
                    list
                ):

                    all_skills = skills

                profile.skills = ", ".join(
                    all_skills
                )

                profile.save()

                return redirect(
                    "jobseeker_profile"
                )

    tenth = Education.objects.filter(
        profile=profile,
        education_type="10th"
    ).first()

    plus_two = Education.objects.filter(
        profile=profile,
        education_type="plus_two"
    ).first()

    degree = Education.objects.filter(
        profile=profile,
        education_type="degree"
    ).first()

    experience = Experience.objects.filter(
        profile=profile
    )

    return render(

        request,

        "accounts/jobseeker_profile.html",

        {

            "profile": profile,

            "tenth": tenth,

            "plus_two": plus_two,

            "degree": degree,

            "experience": experience

        }

    )


@login_required
def profile_view(request):

    profile = Profile.objects.get(user=request.user)

    tenth = Education.objects.filter(
        profile=profile,
        education_type="10th"
    ).first()

    plus_two = Education.objects.filter(
        profile=profile,
        education_type="plus_two"
    ).first()

    degree = Education.objects.filter(
        profile=profile,
        education_type="degree"
    ).first()

    experience = Experience.objects.filter(
        profile=profile
    )

    return render(
        request,
        "accounts/profile_view.html",
        {
            "profile": profile,
            "tenth": tenth,
            "plus_two": plus_two,
            "degree": degree,
            "experience": experience
        }
    )

from .models import CompanyProfile


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
            "company_dashboard"
        )



    return render(

        request,

        "accounts/company_profile.html",

        {
            "profile": profile
        }

    )