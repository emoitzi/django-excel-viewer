from django.db import models

class GroupsManager(models.Manager):
    def required_groups(self):
        return self.get_queryset().filter(required=True)


class AllowedGroup(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=255)
    required = models.BooleanField(default=True)

    objects = GroupsManager()


class AllowedDomain(models.Model):
    domain = models.CharField(max_length=200)
    required = models.BooleanField(default=True)
