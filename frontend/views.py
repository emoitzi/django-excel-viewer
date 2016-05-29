from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.http import Http404
from django.utils.translation import ugettext_lazy as _

from allauth.account.views import login

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
    document_list = Document.objects.all_current()
    paginator = Paginator(document_list, 25)

    page = request.GET.get('page')
    try:
        documents = paginator.page(page)
    except PageNotAnInteger:
        documents = paginator.page(1)
    except EmptyPage:
        documents = paginator.page(paginator.num_pages)

    return render(request, "frontend/document_list.html", {"documents": documents})


class DocumentView(DetailView):
    model = Document
    template_name = "frontend/index.html"

    def get_object(self, queryset=None):
        try:
            pk = self.kwargs.get(self.pk_url_kwarg, None)
            return Document.objects.get_current(pk)
        except Document.DoesNotExist:
            raise Http404(_("No %(verbose_name)s found matching the query") %
                      {'verbose_name': self.get_queryset().model._meta.verbose_name})

    def get_context_data(self, **kwargs):
        context = super(DocumentView, self).get_context_data(**kwargs)
        context['cells'] = Cell.objects.filter(document=self.object)
        return context

document = login_required(DocumentView.as_view())


class DocumentEdit(UpdateView):
    model = Document
    fields = ['file']
    success_url = '/'
    template_name = "frontend/document_form.html"

    def get_object(self, queryset=None):
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        return Document.objects.get_current(pk)

    def form_valid(self, form):
        if 'file' in form.changed_data:
            # new file uploaded, copy current instance
            document = self.object
            document.replaces_id = document.pk
            document.pk = None
            document.created = None
            document.save()
        return HttpResponseRedirect(self.get_success_url())

edit_document = login_required(DocumentEdit.as_view())


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