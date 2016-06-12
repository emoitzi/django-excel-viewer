import os
import tempfile
from unittest.mock import patch
from io import BytesIO

from django.contrib.auth.models import User, Group, Permission
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.urlresolvers import reverse
from django.core import mail
from django.db.models import Q
from django.conf import settings
from django.test import TestCase, override_settings

from model_mommy import mommy

from excel_import.models import Document
from frontend.models import ChangeRequest


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(), MAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class FrontendTest(TestCase):
    _file = None

    def setUp(self):
        User.objects.create_user(username='user', password='password')
        self.client.login(username='user', password='password')

    @property
    def file(self):
        if self._file:
            self._file.seek(0)
            return self._file

        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(BASE_DIR, "excel_import/testdata/test.xlsx")
        f = open(file_path, 'rb')
        io = BytesIO(f.read())

        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.close()

        file = InMemoryUploadedFile(io, None, 'test.xlsx',
                                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', size, None)
        file.seek(0)
        self._file = file
        return file

    def test_edit_document_creates_new_document(self):
        document = Document.objects.create(file=self.file, name="test")

        response = self.client.post(reverse('document:edit', args=[document.pk]),  {'file': self.file,
                                                                                    'name': 'Test',
                                                                                    'status': Document.LOCKED})
        self.assertEqual(302, response.status_code)

        with patch('excel_import.models.Document.parse_file') as parse_file:
            document.refresh_from_db()
            self.assertFalse(document.current)
            self.assertEqual(2, Document.objects.count())
            self.assertIsNone(document.replaces)
            self.assertEqual(Document.OPEN, document.status)

            new_document = Document.objects.get(~Q(pk=document.pk))
            self.assertTrue(new_document.current)
            self.assertEqual(document.id, new_document.replaces_id)
            self.assertEqual(Document.LOCKED, new_document.status)

    def test_user_group_has_change_permission_after_migrate(self):
        user_group = Group.objects.get(name='user')
        permission = Permission.objects.get(codename="add_changerequest", content_type__app_label="frontend")

        self.assertIn(permission, user_group.permissions.all())
        self.assertTrue(user_group)

    @patch('excel_import.models.Document.parse_file')
    def test_new_change_request_sends_mail_to_editors(self, parse_file):
        editor = mommy.make(settings.AUTH_USER_MODEL, email="editor@test.com")
        editor_group, _ = Group.objects.get_or_create(name='editor')
        editor.groups.add(editor_group)

        mommy.make(ChangeRequest)

        self.assertEqual(1, len(mail.outbox))
        self.assertEqual("New change request", mail.outbox[0].subject)
        self.assertListEqual([editor.email], mail.outbox[0].bcc)

    @patch('excel_import.models.Document.parse_file')
    def test_change_request_accepted_sends_email_to_author(self, parse_file):
        change_request = mommy.make(ChangeRequest,
                                    author__email="author@test.com")
        editor = mommy.make(settings.AUTH_USER_MODEL)

        change_request.accepted_by = editor
        change_request.save()

        self.assertEqual(1, len(mail.outbox))
        self.assertEqual("Your change request has been accepted", mail.outbox[0].subject)
        self.assertListEqual([change_request.author.email], mail.outbox[0].to)
