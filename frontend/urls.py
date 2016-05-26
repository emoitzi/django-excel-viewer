from django.conf.urls import url
from frontend import views

urlpatterns = [
    url(r'^(?P<document_id>[0-9]+)/$', views.document, name='document'),
]