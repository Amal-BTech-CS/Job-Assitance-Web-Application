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
    path(
    "company/profile/view/",
    views.company_profile_view,
    name="company_profile_view"
    ),

    path(
    "company/job/create/",
    views.create_job,
    name="create_job"
    ),

    path(
    "company/jobs/",
    views.manage_jobs,
    name="manage_jobs"
    ),

    path(
    "company/edit-job/<int:id>/",
    views.edit_job,
    name="edit_job"
    ),

    path(
    "company/delete-job/<int:id>/",
    views.delete_job,
    name="delete_job"
    ),
    path(
    "jobseeker/cover-letter/",
    views.cover_letter,
    name="cover_letter"
    ),
 

    path(
    "quiz/",
    views.quiz_home,
    name="quiz_home"
    ),

    path(
    "quiz/question/",
    views.quiz_question,
    name="quiz_question"
    ),

    path(
    "quiz/result/",
    views.quiz_result,
    name="quiz_result"
    ),

    path(
    "jobseeker/mock-interview/",
    views.interview_home,
    name="interview_home"
    ),

    path(
    "jobseeker/mock-interview/question/",
    views.interview_question,
    name="interview_question"
    ),

    path(
    "jobseeker/mock-interview/result/",
    views.interview_result,
    name="interview_result"
    ),
    
]