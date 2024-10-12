from xml.etree.ElementTree import Element, indent, tostring
from PyLyX.LyXobj import LyXobj
from PyLyX.loader import one_line


# def correct_formula(formula: str):
#     if formula.startswith('\\[') and formula.endswith('\\]'):
#         return formula
#
#     if formula.startswith('$'):
#         formula = formula[1:]
#     if formula.endswith('$'):
#         formula = formula[:-1]
#     if formula.startswith('\\('):
#         formula = formula[2:]
#     if formula.endswith('\\)'):
#         formula = formula[:-2]
#
#     if formula.startswith('\\['):
#         return formula +'\\]'
#     if formula.endswith('\\]'):
#         return '\\[' + formula

    return '\\(' + formula + '\\)'


def lyxml2xhtml_style(cell, new_cell):
    if cell.tag == 'cell':  # else cell.tag == 'column'
        new_cell.set('data-usebox', cell.get('usebox'))

    style = []
    align = cell.get('alignment')
    valign = cell.get('valignment')
    if align is not None:
        style.append(f'text-align: {align}')
    if valign is not None:
        style.append(f'vertiacl-align: {valign}')
    for side in ('top', 'bottom', 'right', 'left'):
        value = cell.get(f'{side}line')
        if value is not None:
            style.append(f'border-{side}: solid black')
    if style:
        style = '; '.join(style)
        new_cell.set('style', style)

    rowspan = cell.get('multirow')
    colspan = cell.get('multicolumn')
    if rowspan is not None:
        new_cell.set('rowspan', rowspan)
    if colspan is not None:
        new_cell.set('colspan', colspan)


def lyxml2xhtml_cell(cell: Element):
    new_cell = LyXobj('td')
    lyxml2xhtml_style(cell, new_cell)
    text = cell.text
    for e in cell:
        indent(e, space='')
        text += tostring(e, encoding='unicode')
    branch = [new_cell]
    text = text.splitlines(keepends=True)
    for line in text:
        one_line(text, line, branch)
    return new_cell


def lyxml2xhtml(xml: Element):
    new_table = LyXobj('table')
    for info in {'version', 'rows', 'columns'}:
        new_table.set(f'data-{info}', xml.get(info))
    new_table.set('data-tabularvalignment', xml[0].get('tabularvalignment'))

    colgroup = LyXobj('colgroup')
    new_table.append(colgroup)

    for item in xml:
        if item.tag == 'row':
            new_row = LyXobj('tr')
            new_table.append(new_row)
            for cell in item:
                new_cell = lyxml2xhtml_cell(cell)
                new_row.append(new_cell)
        elif item.tag == 'column':
            new_col = LyXobj('col')
            colgroup.append(new_col)
            lyxml2xhtml_style(item, new_col)

    indent(new_table, space='')
    return new_table


def xhtml2lyxml_style(cell, new_cell):
    if cell.tag == 'td':
        new_cell.set('usebox', cell.get('data-usebox'))

    style = cell.get('style')
    if style is not None:
        style = style.split('; ')
        style = [style[i].split(': ') for i in range(len(style))]
        style = dict(style)
        align = style.get('text-align')
        valign = style.get('vertiacl-align')
        if align is not None:
            new_cell.set('alignment', align)
        if valign is not None:
            new_cell.set('valignment', valign)
        for side in ('top', 'bottom', 'right', 'left'):
            value = style.get(f'border-{side}')
            if value is not None and value != 'false':
                new_cell.set(f'{side}line', 'true')

    multirow = cell.get('rowspan')
    multicolumn = cell.get('colspan')
    if multirow is not None:
        new_cell.set('rowspan', multirow)
    if multicolumn is not None:
        new_cell.set('colspan', multicolumn)


def xhtml2lyxml_cell(cell):
    new_cell = Element('cell')
    xhtml2lyxml_style(cell, new_cell)
    for e in cell:
        if e.is_category('Tabular'):
            new_cell.append(xhtml2lyxml(e))
        elif new_cell:
            new_cell[-1].tail += e.obj2lyx()
        else:
            new_cell.text += e.obj2lyx()
    return new_cell


def xhtml2lyxml(table: LyxObj):
    new_table = Element('lyxtabular')
    for info in {'version', 'rows', 'columns'}:
        new_table.set(info, table.get(f'data-{info}'))
    new_table.append(Element('features', {'tabularvalignment': table.get('data-tabularvalignment')}))

    for item in table:
        if item.tag == 'tr':
            new_row = Element('row')
            new_table.append(new_row)
            for cell in item:
                new_cell = xhtml2lyxml_cell(cell)
                new_row.append(new_cell)
        elif item.tag == 'colgroup':
            for col in item:
                new_col = Element('column')
                new_table.append(new_col)
                xhtml2lyxml_style(col, new_col)

    indent(new_table, space='')
    return new_table
