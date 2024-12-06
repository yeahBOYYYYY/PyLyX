from json import load
from os.path import join
from PyLyX.data.data import PACKAGE_PATH, TRANSLATE
from PyLyX.objects.LyXobj import LyXobj, DEFAULT_RANK

with open(join(PACKAGE_PATH, 'lyx2xhtml\\data\\texts.json'), 'r', encoding='utf8') as f:
    TEXTS = load(f)

SECTIONS = ('Part', 'Chapter', 'Section', 'Subsection', 'Subsubsection', 'Paragraph', 'Subparagraph')


def perform_tables(root: LyXobj):
    for table in root.iter('table'):
        table.attrib.update(table[0].attrib)  # tables[0] is <features tabularvalignment="middle">
        table.remove(table[0])

        colgroup = LyXobj('colgroup', 'xml', rank=-DEFAULT_RANK)
        table.insert(0, colgroup)
        lst = [obj for obj in table if obj.tag == 'col']
        for col in lst:
            table.remove(col)
            colgroup.append(col)


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
    for child in list(father):
        if child.category() in ('Labeling', 'Itemize', 'Enumerate', 'Description'):
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
        perform_lists(child)
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
            obj2text(child)
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


def numbering(obj: LyXobj, prefix):
    pre_obj = LyXobj('span', text=prefix+' ')
    pre_obj.attrib['class'] = 'label'
    obj.text, pre_obj.tail = '', obj.text
    obj.insert(0, pre_obj)


def tocing(lst: LyXobj, obj: LyXobj, prefix):
    item = LyXobj('li')
    obj.set('id', obj.attrib['class'].split()[1] + '_' + prefix)
    link = LyXobj('a', attrib={'href': '#' + obj.get('id', '')}, text=prefix+' '+obj.text)
    item.append(link)
    lst.append(item)
    return item


def rec_num_and_toc(toc: LyXobj, element, secnumdepth=-1, tocdepth=-1, prefix='', lang='en'):
    i = 0
    for sec in element.findall('section'):
        if sec.rank() <= max(secnumdepth, tocdepth) and sec is not element:
            if len(sec) and sec.attrib.get('class') in {f'layout {s}' for s in SECTIONS}:
                i += 1
                if sec.rank() <= secnumdepth or sec.rank() <= tocdepth:
                    new_prefix = f'{prefix}.{i}' if prefix else f'{i}'
                    command, category, details = sec.command(), sec.category(), sec.details()
                    if sec.rank() <= 1 and (command in TRANSLATE and category in TRANSLATE[command] and details in TRANSLATE[command][category]):
                        new_prefix = TRANSLATE[command][category][details][lang] + ' ' + new_prefix

                    if sec.rank() <= tocdepth:
                        item = tocing(toc, sec[0], new_prefix)
                        new_toc = LyXobj('ul')
                        item.append(new_toc)
                    else:
                        new_toc = toc
                    if sec.rank() <= secnumdepth:
                        numbering(sec[0], new_prefix)
                    rec_num_and_toc(new_toc, sec, secnumdepth, tocdepth, new_prefix, lang)


def perform_toc(element, toc, lang):
    for sub in element:
        if sub.get('class') == 'inset CommandInset toc':
            title = LyXobj('h2', text=TRANSLATE['inset']['CommandInset']['toc'][lang])
            sub.extend((title, toc))
        else:
            perform_toc(sub, toc, lang)
