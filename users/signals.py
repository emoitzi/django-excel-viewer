from django.contrib.auth.models import Group


def add_to_user_group(sender, **kwargs):
    if kwargs.get("raw", False):
        return

    created = kwargs.get("created", False)
    if created:
        user_group, _ = Group.objects.get_or_create('user')
        instance = kwargs.get("instance")
        instance.groups.add(user_group)