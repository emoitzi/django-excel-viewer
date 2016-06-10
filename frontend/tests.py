import os
import tempfile
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.test import TestCase, RequestFactory, override_settings
from io import BytesIO

from excel_import.models import Document


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
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