from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.contrib.auth.models import Permission, Group


def post_migrate_handler(sender, **kwargs):
    add_change = Permission.objects.get(codename="add_changerequest", content_type__app_label="frontend")

    group = Group.objects.get(name='user')
    group.permissions.add(add_change)


class FrontendConfig(AppConfig):
    name = 'frontend'

    def ready(self):
        post_migrate.connect(post_migrate_handler, sender=self)
