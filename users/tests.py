from unittest.mock import patch

from allauth.socialaccount.models import SocialAccount, SocialLogin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.utils.unittest import TestCase

from model_mommy import mommy

from users.adapter import AccountAdapter, SocialAccountAdapter
from users.models import AllowedGroup


facebook_query_result = {
  "data": [
    {
      "name": "User1",
      "administrator": False,
      "id": "123"
    },
    {
      "name": "User2",
      "administrator": True,
      "id": "1234"
    }
  ],
  "paging": {
    "next": "https://graph.facebook.com/v2.6/1111/members?limit=25&offset=50&format=json&icon_size=16&access_token=EAACEdEose0cBAGrrNEjxF0QZBaZCwhqOwNp5ZBQyrFOruJTKAzFOg83gtdjbiJYq8hl49cWgEVuZCQPMqKo1Dthqxcelnc0keJdCxSb6P4Nxa5ymaKBayRZBZARxx1TKsXI64lM0voZBT9tJRnUMZBeZAXI4jLH6a45oAnUjxOIQWyQZDZD&__after_id=enc_AdCN9znks5OCQNpEZAD9aKNrZAN3nf2TBZC1lZAyWG5cePaJcIZBwdtSoq86T1kJ1aS0c48CDU7SaorlrqMqVFjGvb0Yc",
    "previous": "https://graph.facebook.com/v2.6/1111/members?limit=25&offset=0&format=json&icon_size=16&access_token=EAACEdEose0cBAGrrNEjxF0QZBaZCwhqOwNp5ZBQyrFOruJTKAzFOg83gtdjbiJYq8hl49cWgEVuZCQPMqKo1Dthqxcelnc0keJdCxSb6P4Nxa5ymaKBayRZBZARxx1TKsXI64lM0voZBT9tJRnUMZBeZAXI4jLH6a45oAnUjxOIQWyQZDZD&__before_id=enc_AdC54d95FL2F0ZCkbQqtiFihroJbX2uEfx5jcTlzTzVEMhy8uwLp0pabhaa9ogmOFsH2YErxHj0ZAbgm3VkojtshvZB"
  }
}


class SocialAdapterTestCase(TestCase):

    def test_required_facebook_group(self):
        User = get_user_model()
        user = mommy.prepare(User)
        factory = RequestFactory()
        request = factory.get('/accounts/login/callback/')
        request.user = AnonymousUser()

        mommy.make(AllowedGroup, id='123')
        account = SocialAccount(provider='facebook', uid='123')
        sociallogin = SocialLogin(user=user, account=account)

        adapter = SocialAccountAdapter()
        with patch("users.adapter.SocialAccountAdapter._fb_query") as fb_query:
            fb_query.return_value = facebook_query_result
            self.assertTrue(adapter.check_facebook_groups(sociallogin))

    def test_required_facebook_group_false(self):
        User = get_user_model()
        user = mommy.prepare(User)
        factory = RequestFactory()
        request = factory.get('/accounts/login/callback/')
        request.user = AnonymousUser()

        mommy.make(AllowedGroup, id='123')
        account = SocialAccount(provider='facebook', uid='1111')
        sociallogin = SocialLogin(user=user, account=account)

        adapter = SocialAccountAdapter()
        with patch("users.adapter.SocialAccountAdapter._fb_query") as fb_query:
            fb_query.return_value = facebook_query_result

            self.assertFalse(adapter.check_facebook_groups(sociallogin))

    def test_required_facebook_group_google(self):
        User = get_user_model()
        user = mommy.prepare(User)
        factory = RequestFactory()
        request = factory.get('/accounts/login/callback/')
        request.user = AnonymousUser()

        mommy.make(AllowedGroup, id='123')
        account = SocialAccount(provider='google', uid='1111')
        sociallogin = SocialLogin(user=user, account=account)

        adapter = SocialAccountAdapter()
        with patch("users.adapter.SocialAccountAdapter._fb_query") as fb_query:
            fb_query.return_value = facebook_query_result

            self.assertFalse(adapter.check_facebook_groups(sociallogin))