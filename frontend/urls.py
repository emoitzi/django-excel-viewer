from django.conf.urls import url
from frontend import views

urlpatterns = [
    url(r'^(?P<pk>[0-9]+)/$', views.document, name='document'),
    url(r'^create/$', views.create, name='create'),
    url(r'^(?P<pk>[0-9]+)/edit/', views.edit_document, name='edit'),
    url(r'^$', views.list_documents, name='list'),
]