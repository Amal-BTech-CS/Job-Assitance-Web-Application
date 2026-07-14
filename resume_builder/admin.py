from django.contrib import admin
from .models import Resume


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ("full_name", "target_title", "updated_at")
    search_fields = ("full_name", "target_title", "email")
