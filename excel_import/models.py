from django.db.models import Q
from django.db.models.fields import DateTimeField
from openpyxl import load_workbook
from openpyxl.styles.colors import COLOR_INDEX


from django.core.validators import MinValueValidator
from django.db import models

import logging

logger = logging.getLogger(__name__)


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


class DocumentManager(models.Manager):
    def get_current(self, id):
        instance = self.get_queryset().get((Q(replaces=id) & Q(current=True) & Q(replaces__isnull=False)) |
                                            (Q(id=id)) & Q(current=True) & Q(replaces__isnull=True))
        return instance

    def all_current(self):
        return self.get_queryset().filter(current=True)


class Document(models.Model):
    file = models.FileField(blank=True, null=True)
    replaces = models.ForeignKey('self', blank=True, null=True, )
    name = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    current = models.BooleanField(default=True)

    objects = DocumentManager()

    def save(self, *args, **kwargs):
        parse_file = False
        if not self.pk:
            if self.current:
                Document.objects.filter(Q(replaces=self.replaces) | Q(id=self.replaces_id)) \
                                .update(current=False)
            parse_file = True
        super(Document, self).save(*args, **kwargs)

        if parse_file:
            self.parse_file()

    @property
    def url_id(self):
        return self.replaces_id or self.pk


    def create_colors(self, work_sheet):
        color_set = set()
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
            else:
                # TODO: Add theme colors
                index_set.add(color.value)

        for color in color_set:
            name = ''.join(['color_', str(color)])
            DocumentColors.objects.create(name=name, color=color[2:], document=self)
        for index in index_set:
            name = ''.join(['color_', str(index)])
            DocumentColors.objects.create(name=name, color=str(COLOR_INDEX[index][2:]), document=self)

    def parse_file(self):
        workbook = load_workbook(self.file.path)
        sheet_names = workbook.get_sheet_names()
        work_sheet = workbook[sheet_names[0]]

        start_cells = dict()

        skip_list = work_sheet.merged_cells.copy()
        for range in work_sheet.merged_cell_ranges:
            start, end = range.split(':')
            skip_list.remove(start)

            column_span, row_span = get_span(start, end)
            cell_span = dict()
            if row_span:
                cell_span['row_span'] = row_span
            if column_span:
                cell_span['column_span'] = column_span
            start_cells[start] = cell_span

        self.create_colors(work_sheet)
        logger.info("colors created")
        cell_list = list()
        for row in work_sheet.rows:
            # TODO: Check if all columns have same length
            # TODO: skip empty cells/rows. E.g. skip row if first X(=10?) columns are empty
            # db_row = Row.objects.create(document=self)
            first_cell = True
            for cell in row:
                if cell.coordinate in skip_list:
                    continue
                row_span = None
                column_span = None

                if cell.coordinate in start_cells:
                    row_span = start_cells[cell.coordinate].get('row_span', None)
                    column_span = start_cells[cell.coordinate].get('column_span', None)
                cell_list.append(Cell(coordinate=cell.coordinate,
                     value=cell.value or "",
                     color_name=''.join(['color_', str(cell.fill.fgColor.value)]),
                     row_span=row_span,
                     column_span=column_span,
                     document=self,
                     horizontal_alignment=cell.style.alignment.horizontal,
                    first_cell=first_cell,
                    ))
                first_cell = False
                logger.debug("created cell %s" %cell.coordinate)
        cell_list[len(cell_list) - 1].last_cell=True
        Cell.objects.bulk_create(cell_list)


class Cell(models.Model):
    coordinate = models.CharField(max_length=15)
    value = models.CharField(max_length=255, default="", blank=True)
    color_name = models.CharField(max_length=20)
    row_span = models.IntegerField(blank=True, null=True, validators=MinValueValidator(1))
    column_span = models.IntegerField(blank=True, null=True, validators=MinValueValidator(1))
    document = models.ForeignKey(Document, null=True, blank=True)
    horizontal_alignment = models.CharField(max_length=20, null=True, blank=True)
    first_cell = models.BooleanField(default=False)
    last_cell = models.BooleanField(default=False)

    class Meta:
        ordering = ['id', ]

    @property
    def attributes(self):
        attributes = str()
        if self.row_span:
            attributes = 'rowspan=%d' % self.row_span
        if self.column_span:
            attributes = ''.join([attributes, 'colspan=%d' % self.column_span])
        return attributes

    @property
    def class_tags(self):
        classes = self.color_name
        if self.horizontal_alignment:
            classes = ''.join([classes, ' ', self.horizontal_alignment])
        return classes


class DocumentColors(models.Model):
    name = models.CharField(max_length=20)
    color = models.CharField(max_length=6)
    document = models.ForeignKey(Document)

    class Meta:
        unique_together=(('name', 'document'), )
