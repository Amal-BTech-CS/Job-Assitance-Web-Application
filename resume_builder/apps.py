# tracker/apps.py
from django.apps import AppConfig

class TrackerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'resume_builder'  # <-- Change this from 'tracking' to 'tracker'
