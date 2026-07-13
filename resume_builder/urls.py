from django.urls import path
from . import views
from . import resume_pdf

urlpatterns = [
    path('resume-builder/', views.resume_builder, name='resume_builder'),
    path('resume-builder/generate/', views.resume_generator, name='generate_resume'),
    path('resume-builder/edit/', views.resume_edit, name='resume_edit'),
    path('resume-builder/preview/', views.resume_preview, name='resume_preview'),
    path('resume-builder/download/', resume_pdf.download_resume_pdf, name='download_resume_pdf'),
]