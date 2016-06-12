from curses.ascii import EM

from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.db import models
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User

from excel_import.models import Cell


class ChangeRequest(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL)
    accepted_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='+')
    new_value = models.CharField(max_length=255)
    old_value = models.CharField(max_length=255, blank=True)
    target_cell = models.ForeignKey(Cell)
    created_on = models.DateTimeField(auto_now_add=True)
    accepted_on = models.DateTimeField(null=True, blank=True)


    __original_accepted_by = None
    def __init__(self, *args, **kwargs):
        super(ChangeRequest, self).__init__(*args, **kwargs)
        self.__original_accepted_by = self.accepted_by

    def save(self, *args, **kwargs):
        """
        Gets the current value of the referenced cell
        and copies it to the ChangeRequests old_value field
        :param args:
        :param kwargs:
        :return:
        """
        send_mail = False
        if not self.pk:
            self.old_value = self.target_cell.value
            send_mail = True
            if self.accepted_by:
                self.target_cell.value = self.new_value
                self.target_cell.save()
        super(ChangeRequest, self).save(*args, **kwargs)

        # Send mails after call to super().save, so that mail
        # errors do not abort the save process
        if send_mail:
            self.send_editor_mail()
        if not self.__original_accepted_by and self.accepted_by and \
            not self.author == self.accepted_by:
            self.send_author_accepted_mail()

    def document_url(self):
        domain = Site.objects.get_current().domain
        return ''.join([settings.ACCOUNT_DEFAULT_HTTP_PROTOCOL,
                                '://',
                                domain,
                                reverse('document:document', args=[self.target_cell.document_id])])

    def send_editor_mail(self):
        """
        Send notification mails to all users in group editor.
        Only send if ChangeRequest is not yet accepted
        :return:
        """
        if not self.accepted_by:
            editors = User.objects.filter(groups__name='editor')

            body = render_to_string('frontend/email/new_change_request.txt', {'change_request': self,
                                                                              'document_url': self.document_url()})

            email = EmailMessage(_("New change request", ),
                                 body,
                                 bcc=[user.email for user in editors])
            email.send(fail_silently=True)

    def send_author_accepted_mail(self):
        body = render_to_string('frontend/email/change_request_accepted.txt', {'change_request': self,
                                                                               'document_url': self.document_url()})

        email = EmailMessage(_("Your change request has been accepted"),
                             body,
                             to=[self.author.email])
        email.send()
