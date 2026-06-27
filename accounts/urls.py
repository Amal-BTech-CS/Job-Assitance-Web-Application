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
    # Dashboards
    # ===========================

    path(
        "jobseeker/dashboard/",
        views.jobseeker_dashboard,
        name="jobseeker_dashboard"
    ),

    path(
        "company/dashboard/",
        views.company_dashboard,
        name="company_dashboard"
    ),

    # ===========================
    # Job Seeker Profile
    # ===========================

    path(
        "jobseeker/profile/",
        views.jobseeker_profile,
        name="jobseeker_profile"
    ),

    path(
        "jobseeker/profile/view/",
        views.profile_view,
        name="profile_view"
    ),

    # ===========================
    # Logout
    # ===========================

    path(
        "logout/",
        views.user_logout,
        name="logout"
    ),

    path(
        "company/profile/",
        views.company_profile,
        name="company_profile"
    ),
]