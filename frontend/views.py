from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

from openpyxl import load_workbook

from excel_import.models import Document

def str_to_ord(string):
    if len(string) > 1:
        raise ValueError
    return ord(string[0])


def get_span(start, end):
    start_row = int(start.lstrip('ABCDEFGHIJKLMNOPQRSTUVWXYZ'))
    start_column = str_to_ord(start.rstrip('0123456798'))

    end_row = int(end.lstrip('ABCDEFGHIJKLMNOPQRSTUVWXYZ'))
    end_column = str_to_ord(end.rstrip('0123456798'))

    column_span = end_column - start_column
    row_span = end_row - start_row

    row_span = row_span + 1 if row_span else row_span
    column_span = column_span + 1 if column_span else column_span

    return column_span, row_span


@login_required
def document(request, document_id):
    document = Document.objects.get(id=int(document_id))

    context = {"document": document,
               }
    return render(request, "frontend/index.html", context)
