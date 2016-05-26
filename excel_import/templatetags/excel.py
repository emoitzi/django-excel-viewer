from django import template

from excel_import.models import Document

register = template.Library()


@register.simple_tag
def color_css(document: Document):
    css_template = template.loader.get_template("excel_import/templatetags/color.txt")
    context = {"colors": document.documentcolors_set.all()}
    return css_template.render(context)


