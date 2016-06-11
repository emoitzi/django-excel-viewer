from django.contrib import admin
from users.models import AllowedGroup, AllowedDomain


class GroupAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'required']

admin.site.register(AllowedGroup, GroupAdmin)


class DomainAdmin(admin.ModelAdmin):
    list_display = ['domain', 'required']

admin.site.register(AllowedDomain, DomainAdmin)