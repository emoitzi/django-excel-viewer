from django.apps import AppConfig
from django.db.models.signals import post_save
from users.signals import add_to_user_group


class UserConfig(AppConfig):
    name = 'users'

    def ready(self):
        from django.contrib.auth.models import User
        post_save.connect(add_to_user_group, sender=User)
