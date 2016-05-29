from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.forms.models import ModelForm
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic.edit import CreateView, FormView
from allauth.account.views import login

from openpyxl import load_workbook

from excel_import.models import Document, Cell


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
def list_documents(request):
    document_list = Document.objects.all()
    paginator = Paginator(document_list, 25)

    page = request.GET.get('page')
    try:
        documents = paginator.page(page)
    except PageNotAnInteger:
        documents = paginator.page(1)
    except EmptyPage:
        documents = paginator.page(paginator.num_pages)

    return render(request, "frontend/document_list.html", {"documents": documents})

# @login_required
def document(request, document_id):
    document = Document.objects.get(id=int(document_id))
    cells = Cell.objects.filter(document=document)

    context = {"document": document,
               "cells": cells,
               }
    return render(request, "frontend/index.html", context)


class DocumentCreate(CreateView):
    model = Document
    fields = ['file', 'name']
    success_url = '/'
    template_name = "frontend/document_form.html"

create = login_required(DocumentCreate.as_view())


def index(request):
    if request.user.is_authenticated():
        return render(request, "index.html")
    return login(request)