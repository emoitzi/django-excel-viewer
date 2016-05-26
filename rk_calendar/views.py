from django.http import HttpResponse
from django.shortcuts import render

from openpyxl import load_workbook


def str_to_ord(string):
    if len(string) > 1:
        raise ValueError
    return ord(string[0])


def get_span(start, end):
    start_row = int(start.lstrip('ABCDEFGHIJKLMNOPQRSTUVWXYZ'))
    start_column = str_to_ord(start.rstrip('0123456798'))

    end_row = int(end.lstrip('ABCDEFGHIJKLMNOPQRSTUVWXYZ'))
    end_column = str_to_ord(end.rstrip('0123456798'))

    column_span = end_column - start_column
    row_span = end_row - start_row

    row_span = row_span + 1 if row_span else row_span
    column_span = column_span + 1 if column_span else column_span

    return column_span, row_span




def calendar(request):
    workbook = load_workbook("test.xlsx")
    sheet_names = workbook.get_sheet_names()
    work_sheet = workbook[sheet_names[0]]

    start_cells = dict()


    skip_list = work_sheet.merged_cells.copy()
    for range in work_sheet.merged_cell_ranges:
        start, end = range.split(':')
        skip_list.remove(start)

        column_span, row_span = get_span(start, end)
        cell_span = str()
        if row_span:
            cell_span = 'rowspan=%d' % row_span
        if column_span:
            cell_span += ' colspan=%d' % column_span
        start_cells[start] = cell_span




    # for row in work_sheet.rows:
    #     for cell in row:
    #         if cell

    context = {"rows": work_sheet.rows,
               "skip_list": skip_list,
               "start_cells": start_cells,
               "work_sheet": work_sheet,
               }
    return render(request, "rk_calendar/index.html", context)
