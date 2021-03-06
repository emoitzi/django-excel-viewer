import os

import requests
import logging
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
from django import forms
from django.conf import settings

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.providers.facebook.views import compute_appsecret_proof
from allauth.socialaccount.providers.facebook.provider import GRAPH_API_URL
from allauth.exceptions import ImmediateHttpResponse

from users.models import AllowedGroup, AllowedDomain

logger = logging.getLogger(__name__)


class SocialAccountAdapter(DefaultSocialAccountAdapter):

    def _fb_query(self, token, group_id, url=None):
        params = {'appsecret_proof': compute_appsecret_proof(token.app, token)}
        if url:
            response = requests.get(url, params=params)
        else:
            params['access_token'] = token.token
            response = requests.get(
                ''.join([GRAPH_API_URL, '/', str(group_id), '/members']),
                params=params)
        response.raise_for_status()
        data = response.json()
        return data

    def check_facebook_groups(self, sociallogin):
        allowed_groups = AllowedGroup.objects.required_groups()

        # allow all if not configured
        if not allowed_groups:
            return True

        if not sociallogin.account.provider == 'facebook':
            return False

        for group in allowed_groups:
            next_url = None
            while True:
                data = self._fb_query(sociallogin.token, group.id, next_url)
                next_url = None
                for user in data['data']:
                    if sociallogin.account.uid == user['id']:
                        logger.debug("User with facebook uid %s found"
                                     % user['id'])
                        return True
                try:
                    next_url = data["paging"]["next"]
                except KeyError:
                    break
        logger.info("User with facebook uid %s not found"
                    % sociallogin.account.uid)
        return False

    def pre_social_login(self, request, sociallogin):
        process = sociallogin.state.get('process', None)
        if process == 'connect':
            logger.info("Connecting social account",
                        extra={
                            "user": request.user,
                            "provider": sociallogin.account.provider,
                            "uid": sociallogin.account.uid,
                        })
            return
        if not sociallogin.is_existing:
            if not self.check_facebook_groups(sociallogin):
                logger.warning("Social login denied",
                               extra={
                                   'user uid': sociallogin.account.uid,
                                   'provider': sociallogin.account.provider,
                               })
                raise ImmediateHttpResponse(
                    render(request, "users/fb_group_required.html"))
        logger.info("pre social login",
                    extra={
                        "allauth_process": process,
                        "user": request.user,
                        "provider": sociallogin.account.provider,
                        "user_uid": sociallogin.account.uid,
                    })

    def get_connect_redirect_url(self, request, socialaccount):
        return reverse('user:settings')


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return os.environ.get("EXCEL_VIEWER_SIGNUP_OPEN", "FALSE") == "TRUE"

    def clean_email(self, email):
        if not AllowedDomain.objects.filter(required=True).exists():
            return email

        domain = email.split('@')[1]
        if not AllowedDomain.objects.filter(domain__iexact=domain,
                                            required=True).exists():
            logger.warning("Signup denied with wrong domain",
                           extra={
                               'email': email
                           })
            raise forms.ValidationError(_("Adresses from this domain are not"
                                          " allowed."))

        return email