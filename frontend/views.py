import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse,\
                        HttpResponseForbidden
from django.shortcuts import render
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.http import Http404
from django.utils.translation import ugettext_lazy as _

from allauth.account import views as allauth_views
from allauth.account.forms import SignupForm
from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response

from excel_import.models import Document, Cell
from frontend.models import ChangeRequest
from frontend.serializers import ChangeRequestSerializer

logger = logging.getLogger(__name__)


class PermissionRequiredMixin(object):
    required_permission = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm(self.required_permission):
            return HttpResponseForbidden()

        return super(PermissionRequiredMixin, self).dispatch(request, *args, **kwargs)


@login_required
def list_documents(request):
    document_list = Document.objects.all_current().order_by("-created")
    paginator = Paginator(document_list, 15)

    page = request.GET.get('page')
    try:
        documents = paginator.page(page)
    except PageNotAnInteger:
        documents = paginator.page(1)
    except EmptyPage:
        documents = paginator.page(paginator.num_pages)

    context = {
        "previous":
            documents.previous_page_number()
            if documents.has_previous() else 1,
        "next": documents.next_page_number() if documents.has_next() else 1,
        "documents": documents,
    }

    return render(request, "frontend/document_list.html", context)


class DocumentView(DetailView):
    model = Document
    template_name = "frontend/document_detail.html"

    def get_object(self, queryset=None):
        try:
            pk = self.kwargs.get(self.pk_url_kwarg, None)
            return Document.objects.get_current(pk)
        except Document.DoesNotExist:
            raise Http404(
                _("No %(verbose_name)s found matching the query") % {
                    'verbose_name':
                        self.get_queryset().model._meta.verbose_name
                })

    def get_context_data(self, **kwargs):
        context = super(DocumentView, self).get_context_data(**kwargs)
        context['cells'] = Cell.objects.filter(document=self.object)

        pending_requests = ChangeRequest.objects.filter(
            target_cell__document=self.object,
            status=ChangeRequest.PENDING)
        changes = ChangeRequest.objects.filter(
            target_cell__document=self.object,
            status=ChangeRequest.ACCEPTED)

        context.update({
            'pending_requests': [
                    cell['target_cell_id'] for cell in
                    pending_requests.values('target_cell_id')
                ],
            'changes': [
                    cell['target_cell_id'] for cell in
                    changes.values('target_cell_id')
                 ]
        })
        return context


document_view = login_required(DocumentView.as_view())


class DocumentEdit(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Document
    fields = ['file', 'name', 'status']
    template_name = "frontend/document_form.html"
    success_message = _("%(name)s was updated successfully")
    required_permission = 'excel_import.change_document'

    def get_object(self, queryset=None):
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        return Document.objects.get_current(pk)

    def get_success_url(self):
        document_id = self.object.replaces_id if self.object.replaces \
            else self.object.pk
        return reverse("document:document", args=[document_id])

    def form_valid(self, form):
        copy_change_requests = False
        document = None
        if 'file' in form.changed_data:
            # new file uploaded, copy current instance
            document = form.instance
            document.replaces_id = document.replaces_id or document.pk
            document.pk = None
            document.created = None
            copy_change_requests = True
        form.save()

        if copy_change_requests:
            requests = ChangeRequest.objects.filter(
                target_cell__document_id=document.replaces_id,
                status=ChangeRequest.PENDING)

            for request in requests:
                try:
                    request.target_cell = document.cell_set.get(
                        coordinate=request.target_cell.coordinate)
                    request.save()
                except Cell.DoesNotExist:
                    logger.debug("Cannot find cell with coordinate %s in new "
                                 "document %s(%d)"
                                 % (request.target_cell.coordinate,
                                    document.name, document.pk))
                    pass

        return HttpResponseRedirect(self.get_success_url())


edit_document = login_required(DocumentEdit.as_view())


class DocumentCreate(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = Document
    fields = ['file', 'name', 'status']
    template_name = "frontend/document_form.html"
    success_message = _("%(name)s was created successfully")
    required_permission = 'excel_import.add_document'

    def get_success_url(self):
        return reverse("document:document", args=[self.object.pk])


create = login_required(DocumentCreate.as_view())


class LoginView(allauth_views.LoginView):
    def get_context_data(self, **kwargs):
        context = super(LoginView, self).get_context_data(**kwargs)
        context["signup_form"] = SignupForm()
        return context

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return render(request, "frontend/index.html")
        return super(LoginView, self).get(request)

index = LoginView.as_view()


class ChangeRequestViewSet(viewsets.ModelViewSet):
    queryset = ChangeRequest.objects.all()
    serializer_class = ChangeRequestSerializer

    def create(self, request, *args, **kwargs):
        django_request = getattr(request, "_request")
        change_request = ChangeRequest(author=request.user)
        serializer = self.get_serializer(data=request.data,
                                         instance=change_request)
        serializer.is_valid(raise_exception=True)

        accepted_message = _("Your change request has been accepted."
                             " New value: \"%(new_value)s\"")
        placed_message = _("Your change request has been placed and "
                           "is waiting for review.")

        response_status = status.HTTP_201_CREATED
        target_cell = serializer.validated_data.get("target_cell")
        if target_cell.document.status == Document.OPEN:
            self.perform_create(serializer)
            if not target_cell.changerequest_set.filter(
                    status=ChangeRequest.ACCEPTED).exists():
                change_request.accept(request.user)
                messages.success(
                    django_request,
                    accepted_message % {
                        "new_value": serializer.validated_data.get("new_value")
                        })
            else:
                messages.info(django_request, placed_message)
                response_status = status.HTTP_202_ACCEPTED

        elif target_cell.document.status == Document.REQUEST_ONLY:
            self.perform_create(serializer)
            if request.user.has_perm('frontend.change_changerequest'):
                #  Change requests from editors are accepted immediatly
                change_request.accept(request.user)
                messages.success(
                    django_request, accepted_message %
                    {
                        "new_value": serializer.validated_data.get("new_value")
                    })
            else:
                messages.info(django_request, placed_message)
                response_status = status.HTTP_202_ACCEPTED
        else:
            messages.error(django_request,
                           _("We are sorry, this is not allowed on a locked"
                             " document."))
            response_status = status.HTTP_403_FORBIDDEN

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data,
                        status=response_status,
                        headers=headers)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        django_request = getattr(request, "_request")
        data = None
        if instance.status == ChangeRequest.PENDING and\
                not instance.target_cell.document.status == Document.LOCKED:
            instance.accept(request.user)
            response_status = status.HTTP_200_OK
            data = {"new_value": instance.new_value, }
            messages.success(django_request,
                             _("The change request \"%s\" has been accepted."
                               % instance.new_value))
        else:
            messages.error(django_request,
                           _("You do not have the permission to accept"
                             " requests."))
            response_status = status.HTTP_403_FORBIDDEN
        return Response(status=response_status, data=data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        django_request = getattr(request, "_request")
        if instance.author == request.user and (
            instance.status == ChangeRequest.PENDING or (
                ChangeRequest.objects.filter(
                    target_cell=instance.target_cell,
                    status=ChangeRequest.ACCEPTED)
                .latest('created_on') ==
                instance and
                instance.target_cell.document.status == Document.OPEN)):
            instance.revoke()
            messages.success(django_request, _("Removed successfully."))

            other_requests = ChangeRequest.objects.filter(
                                target_cell=instance.target_cell,
                                status=ChangeRequest.PENDING).exists()
            return Response(status=status.HTTP_200_OK,
                            data={
                                'old_value': instance.old_value,
                                'other_requests': other_requests
                            })
        else:
            messages.error(django_request,
                           _("You cannot withdraw this request."))
            return Response(status=status.HTTP_403_FORBIDDEN)


@login_required
def popover(request, pk):
    requests = ChangeRequest.objects.filter(target_cell__id=pk,
                                            status=ChangeRequest.PENDING)

    context = {
        "requests": requests,
        "is_editor": request.user.groups.filter(name='editor').exists(),
        "cell_id": pk,
        "can_delete": False,
    }

    try:
        last_request = ChangeRequest.objects.filter(
            target_cell_id=pk,
            target_cell__document__status=Document.OPEN,
            status=ChangeRequest.ACCEPTED).latest("reviewed_on")
        if last_request.author == request.user:
            context.update({
                "can_delete": True,
                "request_id": last_request.pk
            })

    except ChangeRequest.DoesNotExist:
        pass

    return render(request, 'frontend/cell_popover.html', context)


@login_required
def download_document(request, pk):
    try:
        document = Document.objects.get(pk=pk)
    except Document.DoesNotExist:
        raise Http404

    xlsx_bytes = document.create_xlsx()
    response = HttpResponse(xlsx_bytes)
    response["Content-Type"] = \
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    response["Content-Length"] = len(xlsx_bytes)
    response['Content-Disposition'] = \
        'attachment; filename="%s.xlsx"' % document.name
    return response
