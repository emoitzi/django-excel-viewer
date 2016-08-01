import os
import tempfile
from unittest.mock import patch
from io import BytesIO

import time
from django.contrib.auth.models import User, Group, Permission
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.urlresolvers import reverse
from django.core import mail
from django.db.models import Q
from django.conf import settings
from django.test import TestCase, override_settings
from rest_framework import status

from model_mommy import mommy

from excel_import.models import Document, Cell
from frontend.models import ChangeRequest, TemporaryDocument
from frontend.views import FILE_SESSION_NAME_KEY, FILE_SESSION_PK_KEY


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(),
                   MAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
                   CELERY_ALWAYS_EAGER=True,)
class FrontendTest(TestCase):
    _file = None

    def setUp(self):
        self.user = User.objects.create_user(username='user', email="", password='password')
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
        temp_file = mommy.make(TemporaryDocument,
                               file=self.file)
        self.user.groups.add(Group.objects.get(name='editor'))
        session = self.client.session
        session[FILE_SESSION_NAME_KEY] = "test.xlsx"
        session[FILE_SESSION_PK_KEY] = temp_file.pk
        session.save()

        response = self.client.post(reverse('document:edit_details', args=[document.pk]), {'worksheet': temp_file.pk,
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
        temp_file = mommy.make(TemporaryDocument,
                               file=self.file)
        self.user.groups.add(Group.objects.get(name='editor'))
        session = self.client.session
        session[FILE_SESSION_NAME_KEY] = "test.xlsx"
        session[FILE_SESSION_PK_KEY] = temp_file.pk
        session.save()

        response = self.client.post(reverse('document:edit_details', args=[document.pk]), {'worksheet': temp_file.pk,
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
        add_change = Permission.objects.get(codename="add_changerequest", content_type__app_label="frontend")
        delete_change = Permission.objects.get(codename="delete_changerequest", content_type__app_label="frontend")

        self.assertIn(add_change, user_group.permissions.all())
        self.assertIn(delete_change, user_group.permissions.all())
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
    def test_new_change_request_sends_mail_to_editors(self, parse_file,):
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
        document = Document.objects.create(file=self.file,
                                           name="Test",
                                           status=Document.REQUEST_ONLY)
        cell = document.cell_set.get(coordinate='A2')
        temp_file = mommy.make(TemporaryDocument,
                               file=self.file)
        author = mommy.make(settings.AUTH_USER_MODEL)
        self.user.groups.add(Group.objects.get(name='editor'))
        change_request = ChangeRequest.objects.create(author=author,
                                                      new_value="test",
                                                      target_cell=cell)

        session = self.client.session
        session[FILE_SESSION_NAME_KEY] = "test.xlsx"
        session[FILE_SESSION_PK_KEY] = temp_file.pk
        session.save()

        response = self.client.post(reverse('document:edit_details',
                                            args=[document.pk]),
                                    {
                                     'name': 'Test',
                                     'worksheet': 0,
                                     'status': Document.REQUEST_ONLY,
                                     })

        self.assertEqual(302, response.status_code)

        self.assertEqual(2, Document.objects.count())
        change_request.refresh_from_db()
        new_document = Document.objects.get(~Q(pk=document.pk))
        new_cell = new_document.cell_set.get(coordinate='A2')

        self.assertEqual(change_request.target_cell, new_cell)

    @patch('excel_import.models.Document.parse_file')
    def test_request_on_open_document(self, parse_file):
        cell = mommy.make(Cell, document__status=Document.OPEN, value="test")

        response = self.client.post("/api/change-request/", {"new_value": "new-value",
                                                             "target_cell": cell.id})

        cell.refresh_from_db()
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual("new-value", cell.value)

        self.assertEqual(1, ChangeRequest.objects.count())

        change_request = ChangeRequest.objects.first()
        self.assertEqual(self.user, change_request.reviewed_by)
        self.assertIsNotNone(change_request.reviewed_on)
        self.assertEqual("test", change_request.old_value)
        self.assertEqual("new-value", change_request.new_value)
        self.assertEqual(ChangeRequest.ACCEPTED, change_request.status)

    @patch('excel_import.models.Document.parse_file')
    def test_second_request_on_open_document(self, parse_file):
        request = mommy.make(ChangeRequest,
                             target_cell__document__status=Document.OPEN,
                             status=ChangeRequest.ACCEPTED,
                             target_cell__value="test",
                             old_value="original_value")

        cell = request.target_cell
        response = self.client.post("/api/change-request/", {"new_value": "new-value",
                                                             "target_cell": cell.id})

        cell.refresh_from_db()
        self.assertEqual(status.HTTP_202_ACCEPTED, response.status_code)
        self.assertEqual("test", cell.value)

        self.assertEqual(2, ChangeRequest.objects.count())

        change_request = ChangeRequest.objects.get(status=ChangeRequest.PENDING)
        self.assertIsNone(change_request.reviewed_by)
        self.assertIsNone(change_request.reviewed_on)
        self.assertEqual("test", change_request.old_value)
        self.assertEqual("new-value", change_request.new_value)
        self.assertEqual("test", cell.value)

    @patch('excel_import.models.Document.parse_file')
    def test_delete_accepted_request_on_open_document(self, parse_file):
        request = mommy.make(ChangeRequest,
                             author=self.user,
                             reviewed_by=self.user,
                             target_cell__document__status=Document.OPEN,
                             status=ChangeRequest.ACCEPTED,
                             target_cell__value="new-value",
                             old_value="old-value")

        response = self.client.delete("/api/change-request/" + str(request.id) + '/')

        request.refresh_from_db()
        cell = Cell.objects.get(pk=request.target_cell_id)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        self.assertEqual("old-value", cell.value)
        self.assertEqual(ChangeRequest.REVOKED, request.status)
        self.assertEqual(self.user, request.reviewed_by)

    @patch('excel_import.models.Document.parse_file')
    def test_cannot_delete_accepted_request_from_other_user_on_open_document(self, parse_file):
        request = mommy.make(ChangeRequest,
                             reviewed_by=self.user,
                             target_cell__document__status=Document.OPEN,
                             status=ChangeRequest.ACCEPTED,
                             target_cell__value="new-value",
                             old_value="old-value")

        response = self.client.delete("/api/change-request/" + str(request.id) + '/')

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    @patch('excel_import.models.Document.parse_file')
    def test_delete_accepted_request_after_later_request_is_accepted_on_open_document(self, parse_file):
        first_request = mommy.make(ChangeRequest,
                                   author=self.user,
                                   reviewed_by=self.user,
                                   target_cell__document__status=Document.OPEN,
                                   status=ChangeRequest.ACCEPTED,
                                   target_cell__value="new-value",
                                   old_value="old-value")
        second_request = mommy.make(ChangeRequest,
                                    target_cell=first_request.target_cell,
                                    status=ChangeRequest.ACCEPTED)

        response = self.client.delete("/api/change-request/" + str(first_request.id) + '/')

        first_request.refresh_from_db()
        second_request.refresh_from_db()

        cell = first_request.target_cell
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertEqual(ChangeRequest.ACCEPTED, first_request.status)
        self.assertEqual("new-value", cell.value)

    @patch('excel_import.models.Document.parse_file')
    def test_request_on_request_only_document(self, parse_file):
        cell = mommy.make(Cell, document__status=Document.REQUEST_ONLY, value="test")

        response = self.client.post('/api/change-request/', {"new_value": "new-value",
                                                             "target_cell": cell.id})

        cell.refresh_from_db()
        request = ChangeRequest.objects.first()

        self.assertEqual(status.HTTP_202_ACCEPTED, response.status_code)
        self.assertEqual(1, ChangeRequest.objects.count())
        self.assertEqual("test", cell.value)
        self.assertEqual("test", request.old_value)
        self.assertEqual("new-value", request.new_value)
        self.assertIsNone(request.reviewed_by)
        self.assertIsNone(request.reviewed_on)
        self.assertEqual(ChangeRequest.PENDING, request.status)

    @patch('excel_import.models.Document.parse_file')
    def test_revoke_pending_request(self, parse_file):
        request = mommy.make(ChangeRequest,
                             status=ChangeRequest.PENDING,
                             author=self.user)

        response = self.client.delete('/api/change-request/' + str(request.id) + '/')

        request.refresh_from_db()
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(ChangeRequest.REVOKED, request.status)
        self.assertEqual(self.user, request.reviewed_by)
        self.assertIsNotNone(request.reviewed_on)

    @patch('excel_import.models.Document.parse_file')
    def test_cannot_revoke_pending_request_of_other_user(self, parse_file):
        request = mommy.make(ChangeRequest,
                             status=ChangeRequest.PENDING,)

        response = self.client.delete('/api/change-request/' + str(request.id) + '/')

        request.refresh_from_db()
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    @patch('excel_import.models.Document.parse_file')
    def test_cannot_revoke_accepted_request(self, parse_file):
        request = mommy.make(ChangeRequest,
                             status=ChangeRequest.ACCEPTED,
                             target_cell__document__status=Document.REQUEST_ONLY,
                             author=self.user)

        response = self.client.delete('/api/change-request/' + str(request.id) + '/')

        request.refresh_from_db()
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    @patch('excel_import.models.Document.parse_file')
    def test_accept_request_with_revoked_requests_on_open_document(self, parse_file):
        request = mommy.make(ChangeRequest,
                             status=ChangeRequest.REVOKED,
                             target_cell__value="test",)
        cell = request.target_cell

        response = self.client.post("/api/change-request/", {"new_value": "new-value",
                                                             "target_cell": cell.id})

        cell.refresh_from_db()
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual("new-value", cell.value)

        self.assertEqual(2, ChangeRequest.objects.count())

        change_request = ChangeRequest.objects.get(~Q(id=request.id))
        self.assertEqual(self.user, change_request.reviewed_by)
        self.assertIsNotNone(change_request.reviewed_on)
        self.assertEqual("test", change_request.old_value)
        self.assertEqual("new-value", change_request.new_value)
        self.assertEqual(ChangeRequest.ACCEPTED, change_request.status)

    @patch('excel_import.models.Document.parse_file')
    def test_editor_can_accept_request(self, parse_file):
        request = mommy.make(ChangeRequest,
                             status=ChangeRequest.PENDING,
                             target_cell__value="old_value",
                             new_value="new_value",)
        self.user.groups.add(Group.objects.get(name='editor'))

        response = self.client.put('/api/change-request/' + str(request.id) + '/')

        request.refresh_from_db()
        cell = Cell.objects.get(id=request.target_cell.id)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual("new_value", cell.value)
        self.assertEqual(ChangeRequest.ACCEPTED, request.status)
        self.assertEqual("old_value", request.old_value)
        self.assertEqual(self.user, request.reviewed_by)
        self.assertIsNotNone(request.reviewed_on)

    @patch('excel_import.models.Document.parse_file')
    def test_editor_cannot_accept_revoked_request(self, parse_file):
        request = mommy.make(ChangeRequest,
                             status=ChangeRequest.REVOKED,
                             target_cell__document__status=Document.REQUEST_ONLY,
                             target_cell__value="old_value",
                             new_value="new_value", )
        self.user.groups.add(Group.objects.get(name='editor'))

        response = self.client.put('/api/change-request/' + str(request.id) + '/')

        request.refresh_from_db()
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    @patch('excel_import.models.Document.parse_file')
    def test_normal_user_cannot_accept_request(self, parse_file):
        request = mommy.make(ChangeRequest,
                             status=ChangeRequest.PENDING,
                             target_cell__document__status=Document.REQUEST_ONLY,
                             target_cell__value="old_value",
                             new_value="new_value", )

        response = self.client.put('/api/change-request/' + str(request.id) + '/')

        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    @patch('excel_import.models.Document.parse_file')
    def test_deny_request_on_locked_document(self, parse_file):
        cell = mommy.make(Cell, document__status=Document.LOCKED, value="test")

        response = self.client.post("/api/change-request/",
                                    {
                                        "new_value": "new-value",
                                        "target_cell": cell.id,
                                    })
        cell.refresh_from_db()
        self.assertEqual(403, response.status_code)
        self.assertEqual("test", cell.value)

    @patch('excel_import.models.Document.parse_file')
    def test_edit_file_creates_temp_file(self, parse_file):
        document = Document.objects.create(file=self.file,
                                           name="Test",
                                           status=Document.REQUEST_ONLY)

        self.user.groups.add(Group.objects.get(name='editor'))

        self.client.post(reverse('document:edit', args=[document.pk]),
                         {
                             'file-file': self.file,
                         })

        self.assertEqual(TemporaryDocument.objects.count(), 1)

    @patch('excel_import.models.Document.parse_file')
    def test_edit_file_redirects_to_details(self, parse_file):
        document = Document.objects.create(file=self.file,
                                           name="Test",
                                           status=Document.REQUEST_ONLY)

        self.user.groups.add(Group.objects.get(name='editor'))

        response = self.client.post(reverse('document:edit', args=[document.pk]),
                                    {
                                        'file-file': self.file,
                                    })

        self.assertRedirects(response, reverse('document:edit_details', args=[document.pk]))

    @patch('excel_import.models.Document.parse_file')
    def test_edit_file_updates_document(self, parse_file):
        document = Document.objects.create(file=self.file,
                                           name="Test",
                                           status=Document.REQUEST_ONLY)

        self.user.groups.add(Group.objects.get(name='editor'))
        parse_file.reset_mock()

        self.client.post(reverse('document:edit', args=[document.pk]),
                                    {
                                        'details-name': 'new-name',
                                        'details-status': Document.LOCKED
                                    })

        parse_file.assert_not_called()
        document.refresh_from_db()
        self.assertEqual(document.name, 'new-name')
        self.assertEqual(document.status, Document.LOCKED)

    @patch('excel_import.models.Document.parse_file')
    def test_edit_file_redirects_to_document(self, parse_file):
        document = Document.objects.create(file=self.file,
                                           name="Test",
                                           status=Document.REQUEST_ONLY)

        self.user.groups.add(Group.objects.get(name='editor'))
        parse_file.reset()

        response = self.client.post(reverse('document:edit', args=[document.pk]),
                                    {
                                        'details-name': 'new-name',
                                        'details-status': Document.LOCKED
                                    })
        self.assertRedirects(response, reverse('document:document', args=[document.pk]))


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(),
                   MAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
                   CELERY_ALWAYS_EAGER=True, )
class ChangeRequestModelTests(TestCase):

    def test_accept(self):
        with patch('excel_import.models.Document.parse_file'):
            cell = mommy.make(Cell)
        author = mommy.make(settings.AUTH_USER_MODEL)
        request = mommy.prepare(ChangeRequest,
                                target_cell=cell,
                                author=author)
        reviewer = mommy.make(User)
        request.accept(reviewer)

        self.assertIsNotNone(request.id)
        self.assertEqual(ChangeRequest.ACCEPTED, request.status)
        self.assertIsNotNone(request.reviewed_on)
        self.assertEqual(reviewer, request.reviewed_by)

    def test_decline(self):
        with patch('excel_import.models.Document.parse_file'):
            cell = mommy.make(Cell)
        author = mommy.make(settings.AUTH_USER_MODEL)
        request = mommy.prepare(ChangeRequest,
                                target_cell=cell,
                                author=author)
        reviewer = mommy.make(User)
        request.decline(reviewer)

        self.assertIsNotNone(request.id)
        self.assertEqual(ChangeRequest.DECLINED, request.status)
        self.assertIsNotNone(request.reviewed_on)
        self.assertEqual(reviewer, request.reviewed_by)

    def test_revoke(self):
        with patch('excel_import.models.Document.parse_file'):
            cell = mommy.make(Cell)
        author = mommy.make(settings.AUTH_USER_MODEL)
        request = mommy.prepare(ChangeRequest,
                                target_cell=cell,
                                author=author)
        mommy.make(User)
        request.revoke()

        self.assertIsNotNone(request.id)
        self.assertEqual(ChangeRequest.REVOKED, request.status)
        self.assertIsNotNone(request.reviewed_on)
        self.assertEqual(author, request.reviewed_by)

    def test_accept_declines_other_requests(self):
        with patch('excel_import.models.Document.parse_file'):
            cell = mommy.make(Cell)
        author = mommy.make(settings.AUTH_USER_MODEL)
        request1 = mommy.make(ChangeRequest,
                              target_cell=cell,
                              author=author,
                              status=ChangeRequest.PENDING)
        request2 = mommy.make(ChangeRequest,
                              target_cell=request1.target_cell,
                              status=ChangeRequest.PENDING)
        reviewer = mommy.make(User)

        request2.accept(reviewer)

        request1.refresh_from_db()
        self.assertEqual(ChangeRequest.DECLINED, request1.status)
        self.assertEqual(reviewer, request1.reviewed_by)
        self.assertIsNotNone(request1.reviewed_on)

    def test_save_sets_old_value_if_empty(self):
        with patch('excel_import.models.Document.parse_file'):
            cell = mommy.make(Cell,
                              value="test")
        author = mommy.make(settings.AUTH_USER_MODEL)
        request = mommy.prepare(ChangeRequest,
                                target_cell=cell,
                                author=author,
                                new_value="new_value")

        request.save()

        self.assertEqual("test", request.old_value)

    def test_save_does_not_set_old_value_when_present(self):
        with patch('excel_import.models.Document.parse_file'):
            cell = mommy.make(Cell, value="cell_value")
        author = mommy.make(settings.AUTH_USER_MODEL)
        request = mommy.prepare(ChangeRequest,
                                target_cell=cell,
                                author=author,
                                old_value="old_value")

        request.save()

        self.assertEqual("old_value", request.old_value)
