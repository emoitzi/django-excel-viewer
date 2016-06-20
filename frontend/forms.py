from django.forms import ModelForm


class ChangeRequestForm(ModelForm):
    class Meta:
        fields = ["new_value"]

