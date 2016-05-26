import os
from django.test import TestCase
from excel_import.models import Document, Row, Cell, DocumentColors


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class ImportTest(TestCase):
    def simple_import(self):
        file = os.path.join(BASE_DIR, "excel_import/testdata/test.xlsx")
        Document.create_document(file)

        self.assertEqual(1, Document.objects.count())
        self.assertEqual(5, Row.objects.count())
        self.assertEqual(67, Cell.objects.count())
        self.assertEqual(3, DocumentColors.objects.count())