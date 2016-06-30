from django.apps import AppConfig




def add_social_account_mail(sender, **kwargs):
    from allauth.account.models import EmailAddress
    request = kwargs.get('request')
    sociallogin = kwargs.get('sociallogin')
    first_address = None
    for email in sociallogin.email_addresses:
        address = EmailAddress.objects.add_email(request,
                                                 request.user,
                                                 email.email)
        first_address = address if not first_address else first_address
    first_address.set_as_primary()

class UserConfig(AppConfig):
    name = 'users'

    def ready(self):
        from users.signals import add_to_user_group
        from allauth.socialaccount.signals import social_account_added
        from django.db.models.signals import post_save
        from django.contrib.auth.models import User
        post_save.connect(add_to_user_group, sender=User)
        social_account_added.connect(add_social_account_mail)