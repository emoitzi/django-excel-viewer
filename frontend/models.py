import logging
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
from frontend.tasks import send_new_status_notification_mail, send_editor_mail
from frontend.utils import get_user_email


logger = logging.getLogger(__name__)


class ChangeRequest(models.Model):
    PENDING = 1
    ACCEPTED = 2
    DECLINED = 3
    REVOKED = 4
    STATUS = (
        (PENDING, _("Pending")),
        (ACCEPTED, _("Accepted")),
        (DECLINED, _("Declined")),
        (REVOKED,  _("Revoked")),
    )

    author = models.ForeignKey(settings.AUTH_USER_MODEL)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                    null=True,
                                    blank=True,
                                    related_name='+')
    new_value = models.CharField(max_length=255)
    old_value = models.CharField(max_length=255, blank=True)
    target_cell = models.ForeignKey(Cell)
    created_on = models.DateTimeField(auto_now_add=True)
    reviewed_on = models.DateTimeField(null=True, blank=True)
    status = models.IntegerField(choices=STATUS, default=PENDING)

    __original_status = None

    class Meta:
        ordering = ['created_on']

    def __str__(self):
        return "pk: %d (%s -> %s)" % (self.pk, self.old_value, self.new_value)

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
            if not self.old_value:
                self.old_value = self.target_cell.value
            send_mail = True
        with transaction.atomic():
            super(ChangeRequest, self).save(*args, **kwargs)

            # Decline all pending requests if one is accepted
            if not self.__original_status == self.status and \
                    self.status == ChangeRequest.ACCEPTED:
                # Manually iterate over all pending requests and call save to
                # trigger notification mails.
                for declined_request in ChangeRequest.objects.filter(
                                    target_cell=self.target_cell,
                                    status=ChangeRequest.PENDING):
                    declined_request.decline(self.reviewed_by)

        if send_mail:
            countdown = settings.EDITOR_MAIL_DELAY or 0
            send_editor_mail.apply_async((self.pk,), countdown=countdown)

        if not self.__original_status == self.status and \
                not self.author == self.reviewed_by:
            send_new_status_notification_mail.delay(self.pk)
        self.__original_status = self.status

    def _review(self, reviewer, status, commit):
        self.reviewed_by = reviewer
        self.status = status
        self.reviewed_on = timezone.now()
        if commit:
            self.save()

    def accept(self, reviewer, commit=True):
        self.target_cell.value = self.new_value
        self.target_cell.save()
        self._review(reviewer, ChangeRequest.ACCEPTED, commit)

    def decline(self, reviewer, commit=True):
        self._review(reviewer, ChangeRequest.DECLINED, commit)

    def revoke(self, commit=True):
        if self.status == ChangeRequest.ACCEPTED:
            self.target_cell.value = self.old_value or ""
            self.target_cell.save()
        self._review(self.author, ChangeRequest.REVOKED, commit)

    def document_url(self):
        domain = Site.objects.get_current().domain
        return ''.join([settings.ACCOUNT_DEFAULT_HTTP_PROTOCOL,
                        '://',
                        domain,
                        reverse('document:document',
                                args=[self.target_cell.document_id])
                        ])

    def send_editor_mail(self):
        """
        Send notification mails to all users in group editor.
        Only send if ChangeRequest is not yet accepted
        :return:
        """
        if self.status == ChangeRequest.PENDING:
            editors = User.objects.filter(groups__name='editor')

            body = render_to_string('frontend/email/new_change_request.txt',
                                    {
                                        'change_request': self,
                                        'document_url': self.document_url()
                                    })

            bcc = []
            for editor in editors:
                bcc.append(get_user_email(editor))

            email = EmailMessage(_("New change request", ),
                                 body,
                                 bcc=bcc)
            email.send()
            logger.info("Sent change request notification mail to editors",
                        extra={
                            'body': body,
                            'bcc': bcc,
                        })

    def send_new_status_notification_mail(self):
        subject, body = "", ""
        if self.status == ChangeRequest.ACCEPTED:
            subject = _("Your change request has been accepted")
            body = render_to_string(
                'frontend/email/change_request_accepted.txt',
                {
                    'change_request': self,
                    'document_url': self.document_url()
                })
        if self.status == ChangeRequest.DECLINED:
            subject = _("Your change request has been declined")
            body = render_to_string(
                'frontend/email/change_request_declined.txt',
                {
                    'change_request': self,
                    'document_url': self.document_url()
                })

        to = get_user_email(self.author)
        email = EmailMessage(subject,
                             body,
                             to=[to])
        email.send(fail_silently=True)
        logger.info("Sent change request status notification mail to author",
                    extra={
                        'body': body,
                        'to': to,
                    })
