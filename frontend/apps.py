from django.apps import AppConfig


def set_frontend_group_permissions(sender, **kwargs):
    from django.contrib.auth.apps import AuthConfig
    from django.contrib.contenttypes.apps import ContentTypesConfig
    from django.contrib.auth.models import Permission, Group
    from excel_import.apps import ExcelImportConfig

    if not type(sender) in [FrontendConfig,
                            ContentTypesConfig,
                            AuthConfig,
                            ExcelImportConfig]:
        return


    try:
        add_change = Permission.objects.get(
            codename="add_changerequest",
            content_type__app_label="frontend")
        delete_change = Permission.objects.get(
            codename="delete_changerequest",
            content_type__app_label="frontend")
        change_change = Permission.objects.get(
            codename="change_changerequest",
            content_type__app_label="frontend")

        group = Group.objects.get(name='user')
        group.permissions.add(add_change, delete_change)
        editor_group = Group.objects.get(name="editor")
        editor_group.permissions.add(add_change, change_change)

        add_document = Permission.objects.get(
            codename="add_document",
            content_type__app_label="excel_import")
        change_document = Permission.objects.get(
            codename="change_document",
            content_type__app_label="excel_import")

        editor_group, _ = Group.objects.get_or_create(name="editor")
        editor_group.permissions.add(add_document, change_document)
    except Permission.DoesNotExist:
        pass


class FrontendConfig(AppConfig):
    name = 'frontend'

    def ready(self):
        from django.db.models.signals import post_migrate, post_save
        from excel_import.models import Document
        from frontend.signals import document_save_handler
        post_migrate.connect(set_frontend_group_permissions)
        post_save.connect(document_save_handler, sender=Document)
