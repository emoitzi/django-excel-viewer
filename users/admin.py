from django.contrib import admin
from users.models import AllowedGroup


class GroupAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'required']

admin.site.register(AllowedGroup, GroupAdmin)