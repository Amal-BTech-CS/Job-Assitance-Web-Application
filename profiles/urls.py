from django.urls import path
from . import views

urlpatterns = [

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
]
