from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.forms import modelform_factory
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils import timezone
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.http import Http404
from django.utils.translation import ugettext_lazy as _

from allauth.account.views import login
from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response

from excel_import.models import Document, Cell
from frontend.models import ChangeRequest
from frontend.serializers import ChangeRequestSerializer


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

        pending_requests = ChangeRequest.objects.filter(target_cell__document=self.object, accepted_by__isnull=True)
        context['pending_requests'] = [cell['target_cell_id'] for cell in pending_requests.values('target_cell_id')]

        changes = ChangeRequest.objects.filter(target_cell__document=self.object, accepted_by__isnull=False)
        context['changes'] = [cell['target_cell_id'] for cell in changes.values('target_cell_id')]
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


class ChangeRequestViewSet(viewsets.ModelViewSet):
    queryset = ChangeRequest.objects.all()
    serializer_class = ChangeRequestSerializer

    def create(self, request, *args, **kwargs):
        change_request = ChangeRequest(author=request.user)
        serializer = self.get_serializer(data=request.data, instance=change_request)
        serializer.is_valid(raise_exception=True)

        response_status = status.HTTP_201_CREATED
        target_cell = serializer.validated_data.get("target_cell")
        if target_cell.document.status == Document.OPEN:
            if not target_cell.changerequest_set.exists():
                change_request.accepted_by = request.user
                change_request.accepted_on = timezone.now()
            else:
                response_status = status.HTTP_202_ACCEPTED
            self.perform_create(serializer)
        elif target_cell.document.status == Document.REQUEST_ONLY:
            response_status = status.HTTP_202_ACCEPTED
            self.perform_create(serializer)
        else:
            response_status = status.HTTP_403_FORBIDDEN

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=response_status, headers=headers)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.accepted_by and not instance.target_cell.document.status == Document.LOCKED:
            instance.target_cell.value = instance.new_value
            instance.target_cell.save()

            instance.accepted_by = request.user
            instance.accepted_on = timezone.now()
            instance.save()
            response_status = status.HTTP_200_OK
        else:
            response_status = status.HTTP_403_FORBIDDEN
        return Response(status=response_status)


def popover(request, pk):

    requests = ChangeRequest.objects.filter(target_cell__id=pk, accepted_by__isnull=True)
    context = {
        "requests": requests,
        "is_editor": request.user.groups.filter(name='editor').exists(),
        "cell_id": pk,
    }
    return render(request, 'frontend/cell_popover.html', context)