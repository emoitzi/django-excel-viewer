from django.conf.urls import url
from rk_calendar import views

urlpatterns = [
    url(r'^(?P<document_id>[0-9]+)/$', views.calendar, name='calendar'),
]