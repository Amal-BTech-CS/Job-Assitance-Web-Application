from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.cache import never_cache

from .forms import JobSeekerRegisterForm, CompanyRegisterForm
from .models import Profile, CompanyProfile, Resume, Skill


def home(request):

    if request.user.is_authenticated:

        if request.user.user_type == "jobseeker":

            profile, created = Profile.objects.get_or_create(
                user=request.user
            )

            resume = Resume.objects.filter(
                profile=profile
            ).first()

            has_skills = False

            if resume:
                has_skills = Skill.objects.filter(
                    resume=resume
                ).exists()

            if profile.full_name and has_skills:

                return redirect(
                    "profile_view"
                )

            else:

                return redirect(
                    "jobseeker_profile"
                )

        elif request.user.user_type == "company":

            return redirect(
                "company_dashboard"
            )

    return render(
        request,
        "accounts/home.html"
    )


def user_logout(request):
    logout(request)
    return redirect('home')


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
                user=user
            )

            return redirect(
                "company_login"
            )

        else:

            print(form.errors)

    else:

        form = CompanyRegisterForm()

    return render(

        request,

        "accounts/company_register.html",

        {
            "form": form
        }

    )


@never_cache
def jobseeker_login(request):

    error = None

    if request.method == "POST":

        username = request.POST.get("username")

        password = request.POST.get("password")

        user = authenticate(

            request,

            username=username,

            password=password

        )

        if user is None:

            from django.contrib.auth import get_user_model

            User = get_user_model()

            try:

                existing_user = User.objects.get(
                    username=username
                )

                error = "Wrong password. Please try again."

            except User.DoesNotExist:

                error = "Username not found. Please register first."

        elif user.user_type != "jobseeker":

            error = "This account is not a Job Seeker account."

        else:

            login(
                request,
                user
            )

            profile, created = Profile.objects.get_or_create(
                user=user
            )

            if profile.full_name:

                return redirect(
                    "jobseeker_dashboard"
                )

            else:

                return redirect(
                    "jobseeker_profile"
                )

    return render(

        request,

        "accounts/jobseeker_login.html",

        {
            "error": error
        }

    )


@never_cache
def company_login(request):

    error = None

    if request.method == "POST":

        username = request.POST.get("username")

        password = request.POST.get("password")

        user = authenticate(

            request,

            username=username,

            password=password

        )

        if user is None:
            from django.contrib.auth import get_user_model

            User = get_user_model()

            try:

                existing_user = User.objects.get(
                    username=username
                )

                error = "Wrong password. Please try again."

            except User.DoesNotExist:

                error = "Username not found. Please register first."

        elif user.user_type != "company":

            error = "This account is not an Employer account."

        else:

            login(
                request,
                user
            )

            profile, created = CompanyProfile.objects.get_or_create(
                user=user
            )

            if profile.company_name:

                return redirect(
                    "company_dashboard"
                )

            else:

                return redirect(

                    "company_profile"
                )

    return render(

        request,

        "accounts/company_login.html",

        {
            "error": error
        }

    )
