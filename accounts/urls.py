from django.urls import path
from . import views

urlpatterns = [

    # Home
    path(
        "",
        views.home,
        name="home"
    ),

    # ===========================
    # Job Seeker Authentication
    # ===========================

    path(
        "jobseeker/register/",
        views.jobseeker_register,
        name="jobseeker_register"
    ),

    path(
        "jobseeker/login/",
        views.jobseeker_login,
        name="jobseeker_login"
    ),

    # ===========================
    # Company Authentication
    # ===========================

    path(
        "company/register/",
        views.company_register,
        name="company_register"
    ),

    path(
        "company/login/",
        views.company_login,
        name="company_login"
    ),

    # ===========================
    # Logout
    # ===========================

    path(
        "logout/",
        views.user_logout,
        name="logout"
    ),
]
