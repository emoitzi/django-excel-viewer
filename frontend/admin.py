from django.contrib import admin

from frontend.models import ChangeRequest


class ChangeRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'author', 'new_value', 'created_on', 'status', 'reviewed_on']
    list_filter = [ 'created_on', 'reviewed_on', 'status']
    search_fields = ['author__username', 'author__last_name', 'author__first_name', 'new_value']


admin.site.register(ChangeRequest, ChangeRequestAdmin)
