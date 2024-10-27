from json import load
from os.path import join
from PyLyX import PACKAGE_PATH
from PyLyX.LyXobj import LyXobj

with open(join(PACKAGE_PATH, 'lyx2xhtml\\data\\texts.json'), 'r', encoding='utf8') as f:
    TEXTS = load(f)

MATHJAX = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js'
CSS_FOLDER = join(PACKAGE_PATH, 'lyx2xhtml\\css')
JS_FOLDER = join(PACKAGE_PATH, 'lyx2xhtml\\js')
BASIC_CSS = 'basic.css'
SECTIONS = ('Part', 'Chapter', 'Section', 'Subsection', 'Subsubsection', 'Paragraph', 'Subparagraph')


def create_script(source: str, async_=''):
    attrib = {'src': source}
    if async_:
        attrib['async'] = async_
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


def order_head(head, css_file=BASIC_CSS, css_folder=CSS_FOLDER):
    css_path = join(css_folder, css_file)
    head.extend((create_script(MATHJAX, 'async'), viewport(), create_css(css_path)))


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


def extract_first_word(obj, edit=False):
    if obj.text:
        first = obj.text.split()[0]
        if edit:
            obj.text = obj.text[len(first):]
        return first

    for e in obj:
        first = extract_first_word(e)
        if first:
            return first

    if obj.tail:
        first = obj.tail.split()[0]
        if edit:
            obj.tail = obj.tail[len(first):]
        return first
    else:
        return False



def order_lists(father):
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
                last = LyXobj(tag)
                children.append(last)


            if child.is_category('Itemize') or child.is_category('Enumerate'):
                last.append(child)
            else:
                first = extract_first_word(child, edit=True)
                prefix = LyXobj('dt', text=first, attrib={'class': child.get('class')})
                item = LyXobj('div', attrib={'class': child.get('class') + ' item'})
                item.extend((prefix, child))
                last.append(item)
        else:
            children.append(child)
        order_lists(child)
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


def order_body(head, body: LyXobj):
    order_tables(body)
    order_lists(body)
    obj2text(body)
    body.append(create_script(join(JS_FOLDER, 'counters.js')))

    for child in head:
        if child.is_command('modules'):
            modules = child.text.split()
            for module in modules:
                module_js = create_script(join(JS_FOLDER, f'modules\\{module}.js'))
                body.append(module_js)


def order_document(head: LyXobj, body: LyXobj, css_file: str, css_folder: str):
    order_head(head, css_file, css_folder)
    order_body(head, body)
    create_title(head, body)
    create_macros(head, body)

