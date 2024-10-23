from json import load
from os.path import join
from PyLyX import PACKAGE_PATH
from PyLyX.LyXobj import LyXobj

with open(join(PACKAGE_PATH, 'lyx2xhtml\\data\\texts.json'), 'r', encoding='utf8') as f:
    TEXTS = load(f)

MATHJAX = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js'
CSS_FOLDER = join(PACKAGE_PATH, 'lyx2xhtml\\css')
BASIC_CSS = join(CSS_FOLDER, 'basic.css')
SECTIONS = ['Part', 'Chapter', 'Sections', 'Subsection', 'Subsubsection', 'Paragraph', 'Subparagraph']


def mathjax():
    attrib = {'src': MATHJAX, 'async': 'async'}
    return LyXobj('script', attrib=attrib)


def create_css(path=BASIC_CSS):
    attrib = {'rel': 'stylesheet', 'type': 'text/css', 'href': path}
    return LyXobj('link', attrib=attrib)


def viewport():
    attrib = {'name': 'viewport', 'content': 'width=device-width'}
    return LyXobj('meta', attrib=attrib)


def create_title(head: LyXobj, body: LyXobj):
    title = body.find('h1')
    if title is not None:
        head_title = LyXobj('title', text=title.text)
        head.append(head_title)


def create_macros(head: LyXobj, body: LyXobj):
    pass


def order_head(head, css_path=BASIC_CSS):
    head.extend((mathjax(), viewport(), create_css(css_path)))
    for child in head:
        if child.is_command('modules'):
            modules = child.text.split()
            for module in modules:
                module_css = create_css(join(CSS_FOLDER, f'modules\\{module}.css'))
                head.append(module_css)
        elif child.is_command('secnumdepth'):
            depth = int(child.get('class')[-1]) + 1
            if depth >= 0:
                depth_css = create_css(join(CSS_FOLDER, f'numbering\\{SECTIONS[depth]}.css'))
                head.append(depth_css)


def order_tables(root: LyXobj):
    for table in root.iter('table'):
        table.attrib.update(table[0].attrib)  # tables[0] is <features tabularvalignment="middle">
        table.remove(table[0])

        colgroup = LyXobj('colgroup')
        table.insert(0, colgroup)
        lst = [obj for obj in table if obj.tag == 'col']
        for col in lst:
            table.remove(col)
            colgroup.append(col)


def order_lists(father):
    last = father
    children = []
    for child in list(father):
        if child.tag == 'li':
            tag = 'ol' if child.is_category('Enumerate') else 'ul'
            class_ = 'enumi' if child.is_category('Enumerate') else 'lyxitemi'
            if last.tag != tag:
                last = LyXobj(tag, attrib={'class': class_})
                children.append(last)
            last.append(child)
        else:
            children.append(child)
        order_lists(child)
        father.remove(child)
    father.extend(children)


def obj2text(root):
    for child in root:
        if child.is_in(TEXTS):
            text = TEXTS[child.command()][child.category()][child.details()]
            if child.is_category('space'):
                text = '\\(' + text + '\\)'
            text += child.tail
            root.text += text
            root.remove(child)
        else:
            obj2text(child)


def correct_formula(formula: str):
    if formula.startswith('\\[') and formula.endswith('\\]'):
        return formula
    elif formula.startswith('\\['):
        return formula +'\\]'
    elif formula.endswith('\\]'):
        return '\\[' + formula
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


def order_body(body: LyXobj):
    order_tables(body)
    order_lists(body)
    obj2text(body)


def order_document(head: LyXobj, body: LyXobj, css_path: str):
    order_head(head, css_path)
    order_body(body)
    create_title(head, body)
    create_macros(head, body)

