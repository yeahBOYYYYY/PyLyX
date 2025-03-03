from json import load
from os.path import join
from PyLyX.data.data import PACKAGE_PATH, RTL_LANGS
from PyLyX.objects.LyXobj import LyXobj, DEFAULT_RANK


def perform_table(table: LyXobj, lang='english'):
    table.attrib.update(table[0].attrib)  # tables[0] is <features tabularvalignment="middle">
    table.remove(table[0])

    colgroup = LyXobj('colgroup', 'xml', rank=-DEFAULT_RANK)
    table.insert(0, colgroup)
    lst = [obj for obj in table if obj.tag == 'column']
    for col in lst:
        table.remove(col)
        colgroup.append(col)
    if lang in RTL_LANGS:
        for row in table.findall('tr'):
            for i in range(len(row)//2):
                row[-1-i][0], row[i][0] = row[i][0], row[-1-i][0]


def extract_first_word(obj, edit=False):
    if obj.text:
        first = obj.text.split()[0]
        if edit:
            obj.text = obj.text[len(first):]
        return first

    for e in obj:
        first = extract_first_word(e, edit)
        if first:
            return first

    if obj.tail:
        first = obj.tail.split()[0]
        if edit:
            obj.tail = obj.tail[len(first):]
        return first
    else:
        return False


def perform_lists(father):
    last = father
    children = []
    for child in list(father):  # list for save the order?
        if child.is_category({'Labeling', 'Itemize', 'Enumerate', 'Description'}):
            if child.is_category('Itemize'):
                tag = 'ul'
            elif child.is_category('Enumerate'):
                tag = 'ol'
            else:
                tag = 'dl'

            if last.tag != tag:
                last = LyXobj(tag, rank=-DEFAULT_RANK)
                children.append(last)


            if child.is_category('Itemize') or child.is_category('Enumerate'):
                last.append(child)
            else:
                first = extract_first_word(child, edit=True)
                prefix = LyXobj('dt', text=first, attrib={'class': child.get('class')}, rank=-DEFAULT_RANK)
                item = LyXobj('div', attrib={'class': child.get('class') + ' item'}, rank=-DEFAULT_RANK)
                item.extend((prefix, child))
                last.append(item)
        else:
            children.append(child)
        father.remove(child)
    father.extend(children)


def correct_formula(formula: str):
    while formula.endswith('\n'):
        formula = formula[:-1]
    if formula.startswith('\\[') and formula.endswith('\\]'):
        return formula
    elif formula.startswith('\\['):
        return formula +'\\]'
    elif formula.startswith('\\begin{'):
        return '\\[' + formula + '\\]'

    if formula.startswith('$'):
        formula = formula[1:]
    if formula.endswith('$'):
        formula = formula[:-1]
    if formula.startswith('\\('):
        formula = formula[2:]
    if formula.endswith('\\)'):
        formula = formula[:-2]
    return '\\(' + formula + '\\)'


def prefixing(obj: LyXobj, prefix, sep=' '):
    pre_obj = LyXobj('span', text=prefix+sep, attrib={'class': 'label'})
    obj.text, pre_obj.tail = '', obj.text
    obj.insert(0, pre_obj)
