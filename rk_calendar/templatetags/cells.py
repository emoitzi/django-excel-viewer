import random
import string

from django import template
from django.shortcuts import render
from django.template.loaders.base import Loader

from openpyxl.styles.colors import COLOR_INDEX


register = template.Library()


@register.simple_tag
def skip(start_cells, cell):
    work_sheet = cell.parent
    if cell.coordinate in work_sheet.merged_cells and cell.coordinate not in start_cells:
        return True
    return False


@register.simple_tag
def attribute(start_cells, cell):
    if cell.coordinate in start_cells:
        return start_cells[cell.coordinate]
    return ""


@register.simple_tag
def cell_class(cell):
    color_name = ''.join(['color_', str(cell.fill.fgColor.value)])
    return "".join(['class=', color_name])


def get_scheme_colors(work_book):
    pass
@register.simple_tag
def color_css(work_sheet):
    theme_colors = get_scheme_colors(work_sheet.parent)

    color_set= set()
    index_set = set()
    for row in work_sheet.rows:
        color = row[0].fill.fgColor

        # skip wrong black values
        if color.value == '00000000':
            continue
        if color.type == 'rgb':
            color_set.add(color.value)
        elif color.type == 'indexed':
            index_set.add(color.value)

    color_list = list()
    for color in color_set:
        name = ''.join(['color_', str(color)])
        color_list.append({"name": name, "value": color[2:]})
    for index in index_set:
        name = ''.join(['color_', str(index)])
        color_list.append({"name": name, "value": str(COLOR_INDEX[index][2:])})

    css_template = template.loader.get_template("rk_calendar/templatetags/color.txt")
    context = {"colors": color_list}
    return css_template.render(context)


