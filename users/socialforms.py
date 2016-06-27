from django import forms
from allauth.socialaccount.forms import SignupForm as SocialAccountSignupForm
from allauth.account import app_settings
from allauth.utils import email_address_exists


class SocialSignupForm(SocialAccountSignupForm):

    def clean_email(self):
        value = self.cleaned_data["email"]
        if app_settings.UNIQUE_EMAIL:
            if value and email_address_exists(value):
                self.raise_duplicate_email_error()
        return value