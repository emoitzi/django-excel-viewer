from django.conf.urls import url
from users import views

urlpatterns = [
    url(r'^$', views.user_settings, name="settings")
        ]