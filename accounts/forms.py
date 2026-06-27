from django import forms
from .models import User


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
            "password"
        ]


    def clean(self):

        cleaned_data = super().clean()

        password = cleaned_data.get("password")

        confirm = cleaned_data.get("confirm_password")


        if password != confirm:

            raise forms.ValidationError(
                "Passwords do not match."
            )


        return cleaned_data




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
            "password"
        ]


    def clean(self):

        cleaned_data = super().clean()

        password = cleaned_data.get("password")

        confirm = cleaned_data.get("confirm_password")


        if password != confirm:

            raise forms.ValidationError(
                "Passwords do not match."
            )


        return cleaned_data