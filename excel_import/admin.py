from django.contrib import admin

from excel_import.models import Document


class DocumentAdmin(admin.ModelAdmin):
    list_display = ['name', 'file', 'status', 'created', 'current']
    list_filter = ['current','created', 'status']
    search_fields = ['name']

admin.site.register(Document, DocumentAdmin)
