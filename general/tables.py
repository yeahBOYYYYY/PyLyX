from xml.etree.ElementTree import fromstring, Element
from PyLyX.general.objects import Environment, LyxObj
from PyLyX.general.helper import *


def code2xml(code: list[str]):
    if not (code[0].startswith(f'<{TABLE_TAG}') and code[-1].endswith(f'</{TABLE_TAG}>')):
        raise Exception('invalid code')
    code = ''.join(code)
    return fromstring(code)


def xml2table(element: Element):
    table = []
    for row in element:
        table.append([])
        for cell in row:
            table[-1].append(cell)
    return table


def xml2xhtml(element: Element, table: Environment):
    for row in element:
        if row.tag == 'row':
            new_row = LyxObj(tag='tr')
            table.append(new_row)
            for cell in row:
                new_cell = LyxObj(tag='td')
                new_row.append(new_cell)
                xml2xhtml_style(cell, new_cell)
    return table


def xhtml2xml(table: Environment):
    new_table = Element('lyxtabular')
    
    for row in table:
        new_row = Element(tag='row')
        new_table.append(new_row)
        for cell in row:
            new_cell = Element(tag='cell')
            new_row.append(new_cell)
            xhtml2xml_style(cell, new_cell)


def xml2xhtml_style(cell, new_cell):
    style = []
    align = cell.get('alignment')
    valign = cell.get('valignment')
    top = cell.get('topline')
    bottom = cell.get('bottomline')
    right = cell.get('rightline')
    left = cell.get('leftline')
    if align is not None:
        style.append(f'text-align: {align}')
    if valign is not None:
        style.append(f'vertiacl-align: {valign}')
    if top is not None:
        style.append(f'border-top: solid black')
    if bottom is not None:
        style.append(f'border-bottom: solid black')
    if right is not None:
        style.append(f'border-right: solid black')
    if left is not None:
        style.append(f'border-left: solid black')
    if style:
        style = '; '.join(style)
        new_cell.set('style', style)


def xhtml2xml_style(cell, new_cell):
    style = cell.get('style')
    style = style.split('; ')
    style = [style[i].split() for i in range(len(style))]
    style = dict(style)

    align = style.get('text-align')
    top = style.get('border-top')
    bottom = style.get('border-bottom')
    right = style.get('border-right')
    left = style.get('border-left')
    if align is not None:
        new_cell.set('alignment', TRUE)
    if top is not None:
        new_cell.set('topline', TRUE)
    if bottom is not None:
        new_cell.set('bottomline', TRUE)
    if right is not None:
        new_cell.set('rightline', TRUE)
    if left is not None:
        new_cell.set('leftline', TRUE)
    new_cell.set('usebox', NONE)
