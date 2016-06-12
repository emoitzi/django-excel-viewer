from curses.ascii import EM

from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.db import models
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.db import transaction

from excel_import.models import Cell


class ChangeRequest(models.Model):
    PENDING = 1
    ACCEPTED = 2
    DECLINED = 3
    STATUS = (
        (PENDING, _("Pending")),
        (ACCEPTED, _("Accepted")),
        (DECLINED, _("Declined")),
    )

    author = models.ForeignKey(settings.AUTH_USER_MODEL)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='+')
    new_value = models.CharField(max_length=255)
    old_value = models.CharField(max_length=255, blank=True)
    target_cell = models.ForeignKey(Cell)
    created_on = models.DateTimeField(auto_now_add=True)
    reviewed_on = models.DateTimeField(null=True, blank=True)
    status = models.IntegerField(choices=STATUS, default=PENDING)

    __original_status = None

    class Meta:
        ordering = ['created_on']

    def __init__(self, *args, **kwargs):
        super(ChangeRequest, self).__init__(*args, **kwargs)
        self.__original_status = self.status

    def save(self, *args, **kwargs):
        """
        Gets the current value of the referenced cell
        and copies it to the ChangeRequests old_value field,
        declines all pending request for the same cell if one
        is accepted, and sends notification mails.
        :param args:
        :param kwargs:
        :return:
        """
        send_mail = False
        if not self.pk:
            self.old_value = self.target_cell.value
            send_mail = True
            if self.reviewed_by:
                self.target_cell.value = self.new_value
                self.target_cell.save()
        with transaction.atomic():
            super(ChangeRequest, self).save(*args, **kwargs)

            # Decline all pending requests if one is accepted
            if not self.__original_status == self.status and \
                    self.status == ChangeRequest.ACCEPTED:
                ChangeRequest.objects.filter(target_cell=self.target_cell, status=ChangeRequest.PENDING) \
                            .update(status=ChangeRequest.DECLINED,
                                    reviewed_by=self.reviewed_by,
                                    reviewed_on=self.reviewed_on,
                                    )

        # Send mails after call to super().save, so that mail
        # errors do not abort the save process
        if send_mail:
            self.send_editor_mail()

        if not self.__original_status == self.status and \
                not self.author == self.reviewed_by:
            self.send_new_status_notification_mail()
        self.__original_status = self.status

    def _review(self, reviewer, status, commit):
        self.reviewed_by = reviewer
        self.status = status
        self.reviewed_on = timezone.now()
        if commit:
            self.save()

    def accept(self, reviewer, commit=True):
        self._review(reviewer, ChangeRequest.ACCEPTED, commit)

    def decline(self, reviewer, commit=True):
        self._review(reviewer, ChangeRequest.DECLINED, commit)

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
        if not self.reviewed_by:
            editors = User.objects.filter(groups__name='editor')

            body = render_to_string('frontend/email/new_change_request.txt', {'change_request': self,
                                                                              'document_url': self.document_url()})

            email = EmailMessage(_("New change request", ),
                                 body,
                                 bcc=[user.email for user in editors])
            email.send(fail_silently=True)

    def send_new_status_notification_mail(self):
        subject, body = "",""
        if self.status == ChangeRequest.ACCEPTED:
            subject = _("Your change request has been accepted")
            body = render_to_string('frontend/email/change_request_accepted.txt', {'change_request': self,
                                                                                   'document_url': self.document_url()})
        if self.status == ChangeRequest.DECLINED:
            subject = _("Your change request has been declined")
            body = render_to_string('frontend/email/change_request_declined.txt', {'change_request': self,
                                                                                   'document_url': self.document_url()})

        email = EmailMessage(subject,
                             body,
                             to=[self.author.email])
        email.send()
