from django import forms
from .models import User


# ==========================================
# Job Seeker Registration Form
# ==========================================

class JobSeekerRegisterForm(forms.ModelForm):

    password = forms.CharField(
        widget=forms.PasswordInput()
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput()
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
        ]

    def clean(self):

        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError(
                "Passwords do not match."
            )

        return cleaned_data

    def save(self, commit=True):

        user = super().save(commit=False)

        user.set_password(
            self.cleaned_data["password"]
        )

        user.user_type = "jobseeker"

        if commit:
            user.save()

        return user


# ==========================================
# Company Registration Form
# ==========================================

class CompanyRegisterForm(forms.ModelForm):

    password = forms.CharField(
        widget=forms.PasswordInput()
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput()
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
        ]

    def clean(self):

        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError(
                "Passwords do not match."
            )

        return cleaned_data

    def save(self, commit=True):

        user = super().save(commit=False)

        user.set_password(
            self.cleaned_data["password"]
        )

        user.user_type = "company"

        if commit:
            user.save()

        return user
    

class ApplicationForm(forms.Form):

    RESUME_CHOICES = (
        ("profile", "Use Profile Resume"),
        ("new", "Upload New Resume"),
    )

    resume_option = forms.ChoiceField(
        choices=RESUME_CHOICES,
        widget=forms.RadioSelect
    )

    new_resume = forms.FileField(
        required=False
    )

    cover_letter = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            "rows": 6,
            "placeholder": "Write your cover letter..."
        })
    )

    # ==========================
    # CLEAN VALIDATION LOGIC
    # ==========================
    def clean(self):
        cleaned_data = super().clean()

        resume_option = cleaned_data.get("resume_option")
        new_resume = cleaned_data.get("new_resume")

        # If user chooses NEW resume → file is mandatory
        if resume_option == "new" and not new_resume:
            self.add_error(
                "new_resume",
                "Please upload a resume file."
            )

        return cleaned_data