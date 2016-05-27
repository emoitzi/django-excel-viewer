from django.conf.urls import url
from frontend import views

urlpatterns = [
    url(r'^(?P<document_id>[0-9]+)/$', views.document, name='document'),
    url(r'^create/$', views.create, name='create'),
    url(r'^$', views.list_documents, name='list'),
]