from json import load
from os.path import join
from data.data import PACKAGE_PATH, RTL_LANGS
from objects.LyXobj import LyXobj, DEFAULT_RANK

with open(join(PACKAGE_PATH, 'lyx2xhtml\\data\\texts.json'), 'r', encoding='utf8') as f:
    TEXTS = load(f)


def perform_table(table: LyXobj, lang='english'):
    table.attrib.update(table[0].attrib)  # tables[0] is <features tabularvalignment="middle">
    table.remove(table[0])

    colgroup = LyXobj('colgroup', 'xml', rank=-DEFAULT_RANK)
    table.insert(0, colgroup)
    lst = [obj for obj in table if obj.tag == 'col']
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


def perform_list(father):
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


def obj2text(root):
    last = root
    for child in root:
        if child.is_in(TEXTS):
            text = TEXTS[child.command()][child.category()][child.details()]
            if child.is_category('space'):
                text = '\\(' + text + '\\)'
            text += child.tail
            if last is root:
                last.text += text
            else:
                last.tail += text
            root.remove(child)
        else:
            last = child


def correct_formula(formula: str):
    if formula.startswith('\\[') and formula.endswith('\\]'):
        return formula
    elif formula.startswith('\\[') and formula.endswith('\\]\n'):
        return formula
    elif formula.startswith('\\[') and formula.endswith('\\]\n\n'):
        return formula[:-1]
    elif formula.startswith('\\['):
        return formula +'\\]'
    elif formula.endswith('\\]\n'):
        return '\\[' + formula
    elif formula.startswith('\\begin{'):
        return '\\[' + formula + '\\]'

    if formula.startswith('$'):
        formula = formula[1:]
    if formula.endswith('$'):
        formula = formula[:-1]
    if formula.endswith('$\n'):
        formula = formula[:-2]
    if formula.startswith('\\('):
        formula = formula[2:]
    if formula.endswith('\\)'):
        formula = formula[:-2]
    if formula.endswith('\\)\n'):
        formula = formula[:-3]
    return '\\(' + formula + '\\)'


def prefixing(obj: LyXobj, prefix, sep=' '):
    pre_obj = LyXobj('span', text=prefix+sep, attrib={'class': 'label'})
    obj.text, pre_obj.tail = '', obj.text
    obj.insert(0, pre_obj)
