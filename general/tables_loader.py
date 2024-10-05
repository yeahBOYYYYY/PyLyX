from xml.etree.ElementTree import Element, tostring, indent
from PyLyX.general.objects import LyxObj, Environment


def lyxml2xhtml_style(cell, new_cell):
    if cell.tag == 'cell':
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
    new_cell = LyxObj('td')
    new_cell.text = cell.text
    lyxml2xhtml_style(cell, new_cell)
    for e in cell:
        if e.tag == 'lyxtabular':
            new_cell.append(lyxml2xhtml(e))
        elif new_cell:
            new_cell[-1].tail += tostring(e, encoding='unicode')
        else:
            new_cell.text += tostring(e, encoding='unicode')
    return new_cell


def lyxml2xhtml(xml: Element):
    new_table = LyxObj('table')
    for info in {'version', 'rows', 'columns'}:
        new_table.set(f'data-{info}', xml.get(info))
    new_table.set('data-tabularvalignment', xml[0].get('tabularvalignment'))

    colgroup = LyxObj('colgroup')
    new_table.append(colgroup)

    for item in xml:
        if item.tag == 'row':
            new_row = LyxObj('tr')
            new_table.append(new_row)
            for cell in item:
                new_cell = lyxml2xhtml_cell(cell)
                new_row.append(new_cell)
        elif item.tag == 'column':
            new_col = LyxObj('col')
            colgroup.append(new_col)
            lyxml2xhtml_style(item, new_col)

    indent(new_table, space='')
    return new_table


def is_table(table):
    if (type(table) is not list) or (not table):
        return False
    length = len(table)
    width = len(table[0])
    for row in range(length):
        if len(table[row]) != width:
            return False
        for col in range(width):
            if type(table[row][col]) not in (str, Environment):
                return False
    return True


def create_cell(align='left', valign='top', border_top='true', border_bottom='false', border_left='true', border_right='false', usebox='none'):
    cell = LyxObj('td')
    style = ['text-align: ' + align, 'vertiacl-align: ' + valign, 'border-top: ' + border_top, 'border-bottom: ' + border_bottom,
              'border-left: ' + border_left, 'border-right: ' + border_right]
    style = '; '.join(style)
    cell.set('style', style)
    cell.set('data-usebox', usebox)
    return cell


def create_table(table: list[list], tabularvalignment='middle', align='left', valign='top', version=3):
    if is_table(table):
        length = len(table)
        width = len(table[0])
    else:
        raise TypeError(f'invalid table: {table}')

    root = LyxObj('table')
    root.attrib = {'data-version': str(version), 'data-rows': str(length), 'data-columns': str(width), 'data-tabularvalignment': tabularvalignment}
    colgroup = LyxObj('colgroup')
    root.append(colgroup)

    for _ in range(width):
        column = LyxObj('col')
        style = f'text-align: {align}; vertiacl-align: {valign}'
        column.set('style', style)
        colgroup.append(column)

    for i in range(length):
        row = LyxObj('tr')
        root.append(row)
        for j in range(width):
            r = 'true' if j == width - 1 else 'false'
            b = 'true' if i == length - 1 else 'false'
            cell = create_cell(border_bottom=b, border_right=r)
            row.append(cell)

            content = table[i][j]

            father = Environment('layout', 'Plain', 'Layout')
            if type(content) is str:
                father.text = content
            else:  # i.e. type(content) in CLASSES
                father.append(content)
            content = Environment('inset', 'Text')
            content.append(father)
            cell.append(content)

    return root
