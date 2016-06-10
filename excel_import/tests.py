import os
from unittest.mock import patch
from django.test import TestCase, override_settings
from excel_import.models import Document, Cell, DocumentColors


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class ImportTest(TestCase):

    @override_settings(MEDIA_ROOT=os.path.join(BASE_DIR, "excel_import/testdata/"))
    def test_simple_import(self):
        file = os.path.join(BASE_DIR, "excel_import/testdata/test.xlsx")
        Document.objects.create(file=file, name="test")

        self.assertEqual(1, Document.objects.count())
        self.assertEqual(67, Cell.objects.count())
        self.assertEqual(3, DocumentColors.objects.count())

    @override_settings(MEDIA_ROOT=os.path.join(BASE_DIR, "excel_import/testdata/"))
    def test_save_on_existing_current_document_does_parse(self):
        file = os.path.join(BASE_DIR, "excel_import/testdata/test.xlsx")
        document = Document.objects.create(file=file, name="test")

        with patch('excel_import.models.Document.parse_file') as parse_file:
            document.save()
            self.assertFalse(parse_file.called)

    @override_settings(MEDIA_ROOT=os.path.join(BASE_DIR, "excel_import/testdata/"))
    def test_save_on_existing_not_current_document_does_not_parse(self):
        file = os.path.join(BASE_DIR, "excel_import/testdata/test.xlsx")
        document = Document.objects.create(file=file, name="test")

        with patch('excel_import.models.Document.parse_file') as parse_file:
            document.save()
            self.assertFalse(parse_file.called)
