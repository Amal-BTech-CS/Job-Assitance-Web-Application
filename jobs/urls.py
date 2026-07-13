from django.urls import path
from . import views

urlpatterns = [

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
        "jobs/",
        views.browse_jobs,
        name="browse_jobs"
    ),
]
