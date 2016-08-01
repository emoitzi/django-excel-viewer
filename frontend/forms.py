from django import forms
from django.conf import settings
from django.forms import ModelForm

from excel_import.models import Document
from excel_import.utils import list_worksheets_from_file
from frontend.models import TemporaryDocument


class ChangeRequestForm(ModelForm):
    class Meta:
        fields = ["new_value"]


class TempFileForm(forms.ModelForm):
    """
    Form to upload temporary files
    """
    class Meta:
        model = TemporaryDocument
        fields = ['file']


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['name', 'status']


class DocumentDetailForm(forms.ModelForm):
    """
    For for document detail views
    """
    def __init__(self, *args, **kwargs):
        self.file = kwargs.pop("file")

        super(DocumentDetailForm, self).__init__(*args, **kwargs)

        worksheet_choices = list_worksheets_from_file(self.file.path)
        self.fields["worksheet"].widget = forms.Select(
            choices=worksheet_choices)

    def save(self, commit=True):
        document = super(DocumentDetailForm, self).save(commit=False)
        document.file = self.file

        if commit:
            document.save()
        return document

    class Meta:
        model = Document
        fields = ['name', 'status', 'worksheet']
