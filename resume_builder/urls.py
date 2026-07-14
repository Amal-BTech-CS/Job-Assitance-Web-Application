from django.urls import path
from . import views

urlpatterns = [
    path('resume_builder/', views.resume_builder, name='resume_builder'),
    path('generate/', views.resume_generator, name='generate_resume'),
    path('edit/', views.resume_edit, name='resume_edit'),
    path('preview/', views.resume_preview, name='resume_preview'),
    path('download/', views.download_resume_pdf, name='download_resume_pdf'),
]
