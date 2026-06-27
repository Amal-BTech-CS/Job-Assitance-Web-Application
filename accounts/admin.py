from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    User,
    Profile,
    Education,
    Experience,
    CompanyProfile
)


admin.site.register(User, UserAdmin)

admin.site.register(Profile)

admin.site.register(Education)

admin.site.register(Experience)

admin.site.register(CompanyProfile)