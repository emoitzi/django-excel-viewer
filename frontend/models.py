from django.db import models
from django.conf import settings

from excel_import.models import Cell


class ChangeRequest(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL)
    accepted_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='+')
    new_value = models.CharField(max_length=255)
    old_value = models.CharField(max_length=255, blank=True)
    target_cell = models.ForeignKey(Cell)
    created_on = models.DateTimeField(auto_now_add=True)
    accepted_on = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.old_value = self.target_cell.value
            if self.accepted_by:
                self.target_cell.value = self.new_value
                self.target_cell.save()
        super(ChangeRequest, self).save(*args, **kwargs)
