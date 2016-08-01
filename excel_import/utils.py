from openpyxl import load_workbook


def list_worksheets_from_file(filename):
    workbook = load_workbook(filename)
    worksheets = workbook.worksheets
    return [(i, worksheets[i].title) for i in range(0,len(worksheets))]