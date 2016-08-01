from django import template
from django.forms.fields import BooleanField, FileField
register = template.Library()


@register.filter(name='label_tag_css')
def label_tag(field, css):
    return field.label_tag(attrs={'class': css})


@register.filter(name='addcss')
def add_attributes(field, css):
    attrs = field.field.widget.attrs
    definition = css.split(',')

    if not isinstance(field.field, BooleanField) and \
       not isinstance(field.field, FileField):
        for d in definition:
            if ':' not in d:
                current_class = attrs.get('class', "")
                attrs['class'] = " ".join([current_class, d])
            else:
                t, v = d.split(':')
                current_t = attrs.get(t, "")
                attrs[t] = " ".join([current_t, v])

    return field.as_widget(attrs=attrs)
