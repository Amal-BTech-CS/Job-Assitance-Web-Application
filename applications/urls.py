from django.urls import path
from . import views

urlpatterns = [

    path(
        "job/<int:job_id>/apply/",
        views.apply_job,
        name="apply_job"
    ),

    path(
        "my_applications/",
        views.my_applications,
        name="my_applications"
    ),

    path(
        "job/<int:job_id>/applicants/",
        views.job_applicants,
        name="job_applicants"
    ),

    path(
        "application/<int:application_id>/",
        views.applicant_detail,
        name="applicant_detail"
    ),
    path(
    "applications/<int:application_id>/",
    views.application_detail,
    name="application_detail",
    ),
    path("application/<int:application_id>/update-status/",
        views.update_application_status,
        name="update_application_status"),
    
]
