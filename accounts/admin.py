from django.contrib import admin

from .models import (
    User,
    Profile,
    Resume,
    Education,
    Experience,
    Skill,
    Project,
    CompanyProfile,
    Job,
    Application,
)

admin.site.register(User)
admin.site.register(Profile)
admin.site.register(Resume)
admin.site.register(Education)
admin.site.register(Experience)
admin.site.register(Skill)
admin.site.register(Project)
admin.site.register(CompanyProfile)
admin.site.register(Job)
admin.site.register(Application)