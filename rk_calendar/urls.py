from django.conf.urls import url
from rk_calendar import views

urlpatterns = [
    url(r'^', views.calendar, name='calendar'),
]