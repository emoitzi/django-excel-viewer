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
from django.utils import timezone

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

    @patch('excel_import.models.Document.parse_file')
    def test_edit_document_creates_new_document(self, parse_file):
        document = Document.objects.create(file=self.file, name="Test")
        parse_file.reset_mock()

        response = self.client.post(reverse('document:edit', args=[document.pk]),  {'file': self.file,
                                                                                    'name': 'Test',
                                                                                    'status': Document.LOCKED})
        self.assertEqual(302, response.status_code)
        parse_file.assert_any_call()
        document.refresh_from_db()
        self.assertFalse(document.current)
        self.assertEqual(2, Document.objects.count())
        self.assertIsNone(document.replaces)
        self.assertEqual(Document.OPEN, document.status)

        new_document = Document.objects.get(~Q(pk=document.pk))
        self.assertTrue(new_document.current)
        self.assertEqual(document.id, new_document.replaces_id)
        self.assertEqual(Document.LOCKED, new_document.status)

    @patch('excel_import.models.Document.parse_file')
    def test_edit_document_sets_correct_replaces_id_on_second_revision(self, parse_file):
        document = Document.objects.create(file=self.file, name="Test", current=False)
        document2 = Document.objects.create(file=self.file, name="Test", current=True, replaces=document)
        parse_file.reset_mock()

        response = self.client.post(reverse('document:edit', args=[document.pk]),  {'file': self.file,
                                                                                    'name': 'Test',
                                                                                    'status': Document.LOCKED})
        self.assertEqual(302, response.status_code)
        parse_file.assert_any_call()
        document2.refresh_from_db()
        self.assertFalse(document2.current)
        self.assertEqual(3, Document.objects.count())

        new_document = Document.objects.get(~Q(pk=document.pk) & ~Q(pk=document2.pk))
        self.assertTrue(new_document.current)
        self.assertEqual(document.id, new_document.replaces_id)

    def test_user_group_has_change_permission_after_migrate(self):
        user_group = Group.objects.get(name='user')
        permission = Permission.objects.get(codename="add_changerequest", content_type__app_label="frontend")

        self.assertIn(permission, user_group.permissions.all())
        self.assertTrue(user_group)

    def test_editor_group_has_permissions_after_migrate(self):
        editor_group = Group.objects.get(name="editor")

        add_change = Permission.objects.get(codename="add_changerequest", content_type__app_label="frontend")
        change_change = Permission.objects.get(codename="change_changerequest", content_type__app_label="frontend")
        add_document = Permission.objects.get(codename="add_document", content_type__app_label="excel_import")
        change_document = Permission.objects.get(codename="change_document", content_type__app_label="excel_import")

        permissions = editor_group.permissions.all()
        self.assertIn(add_change, permissions)
        self.assertIn(change_change, permissions)
        self.assertIn(add_document, permissions)
        self.assertIn(change_document, permissions)


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

        change_request.accept(editor)

        self.assertEqual(1, len(mail.outbox))
        self.assertEqual("Your change request has been accepted", mail.outbox[0].subject)
        self.assertListEqual([change_request.author.email], mail.outbox[0].to)

    def test_edit_document_copies_pending_change_requests(self):
        document = Document.objects.create(file=self.file, name="Test", status=Document.REQUEST_ONLY)
        cell = document.cell_set.get(coordinate='A2')
        author = mommy.make(settings.AUTH_USER_MODEL)

        change_request = ChangeRequest.objects.create(author=author, new_value="test", target_cell=cell)

        response = self.client.post(reverse('document:edit', args=[document.pk]), {'file': self.file,
                                                                                   'name': 'Test',
                                                                                   'status': Document.REQUEST_ONLY})

        self.assertEqual(302, response.status_code)

        self.assertEqual(2, Document.objects.count())
        change_request.refresh_from_db()
        new_document = Document.objects.get(~Q(pk=document.pk))
        new_cell = new_document.cell_set.get(coordinate='A2')

        self.assertEqual(change_request.target_cell, new_cell)