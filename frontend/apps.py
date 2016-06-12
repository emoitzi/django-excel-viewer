from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.contrib.auth.models import Permission, Group


def post_migrate_handler(sender, **kwargs):

    if sender.name == 'frontend':
        add_change = Permission.objects.get(codename="add_changerequest", content_type__app_label="frontend")
        change_change = Permission.objects.get(codename="change_changerequest", content_type__app_label="frontend")

        group = Group.objects.get(name='user')
        group.permissions.add(add_change)
        editor_group = Group.objects.get(name="editor")
        editor_group.permissions.add(add_change, change_change)

    if sender.name == 'excel_import':
        add_document = Permission.objects.get(codename="add_document", content_type__app_label="excel_import")
        change_document = Permission.objects.get(codename="change_document", content_type__app_label="excel_import")

        editor_group, _ = Group.objects.get_or_create(name="editor")
        editor_group.permissions.add(add_document, change_document)


class FrontendConfig(AppConfig):
    name = 'frontend'

    def ready(self):
        post_migrate.connect(post_migrate_handler)
