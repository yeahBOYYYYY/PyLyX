from json import load
from os.path import join, exists
from PyLyX.data.data import PACKAGE_PATH
from PyLyX.objects.LyXobj import LyXobj

with open(join(PACKAGE_PATH, 'lyx2xhtml\\data\\texts.json'), 'r', encoding='utf8') as f:
    TEXTS = load(f)

MATHJAX = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js'
CSS_FOLDER = join(PACKAGE_PATH, 'lyx2xhtml\\css')
BASIC_LTR_CSS = 'basic_ltr.css'
BASIC_RTL_CSS = 'basic_rtl.css'
JS_FOLDER = join(PACKAGE_PATH, 'lyx2xhtml\\js')
NUM_TOC = 'numbering_and_toc.js'
SECTIONS = ('Part', 'Chapter', 'Section', 'Subsection', 'Subsubsection', 'Paragraph', 'Subparagraph')
RTL_LANGS = {'hebrew': 'He-IL'}


def create_script(source: str, async_=''):
    attrib = {'src': source}
    if async_:
        attrib['async'] = async_
    return LyXobj('script', attrib=attrib)


def create_css(path: str):
    attrib = {'rel': 'stylesheet', 'type': 'text/css', 'href': path}
    return LyXobj('link', attrib=attrib)


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


def viewport():
    attrib = {'name': 'viewport', 'content': 'width=device-width'}
    return LyXobj('meta', attrib=attrib)


def create_title(head: LyXobj, body: LyXobj):
    title = body.find('h1')
    if title is not None:
        head_title = LyXobj('title', text=title.text)
        head.append(head_title)


def perform_lang(root, head):
    for lang in RTL_LANGS:
        language = head.find(f'meta[@class="language {lang}"]').text.split()
        if language is not None:
            head.append(create_css(join(CSS_FOLDER, BASIC_RTL_CSS)))
            root.set('lang', RTL_LANGS[lang])
            break
    else:
        head.append(create_css(join(CSS_FOLDER, BASIC_LTR_CSS)))


def pre_design(root):
    root.set('xmlns', 'http://www.w3.org/1999/xhtml')
    head, body = root[0], root[1]
    head.extend((create_script(MATHJAX, 'async'), viewport()))
    create_title(head, body)
    order_tables(body)
    order_lists(body)
    obj2text(body)


def num_and_toc(element, secnumdepth=-1, tocdepth=-1, prefix=''):
    i = 0
    for sub in element:
        if sub.tag == 'section' and sub.rank() <= max(secnumdepth, tocdepth):
            if len(sub) and sub[0].attrib.get('class', '') in {f'layout {sec}' for sec in SECTIONS}:
                i += 1
                sub.set('id', sub.attrib['class'].split()[1])
                title = sub[0]
                if sub.rank() <= secnumdepth:
                    pre = LyXobj('span', text=f'{prefix}.{i} ')
                    title.text, pre.tail = '', title.text
                    title.insert(0, pre)
                if sub.rank() <= tocdepth:
                    pass  # todo:
            num_and_toc(sub, secnumdepth, tocdepth, f'{prefix}.{i}')


def extract_depths(head):
    secnumdepth = tocdepth = -1
    for i in range(-1, 7):
        if head.find(f'meta[@class="secnumdepth {i}"]'):
            secnumdepth = i
        if head.find(f'meta[@class="tocdepth {i}"]'):
            tocdepth = i
    return secnumdepth, tocdepth



def css_and_js(head, body, css_files=(), js_files=()):
    for file in css_files:
        head.append(create_css(file))
    for file in js_files:
        body.append(create_script(file))


def perform_modules(head, body):
    modules = head.find('meta[@class="modules"]').text.split()
    for m in modules:
        path = join(PACKAGE_PATH, 'modules', f'{m}.py')
        if exists(path):
            pass  # todo: perform module
        else:
            print(f'unknown module: {m}.')


def designer(root, css_files=(), js_files=()):
    head, body = root[0], root[1]
    perform_lang(root, head)
    secnumdepth, tocdepth = extract_depths(head)
    num_and_toc(body, secnumdepth, tocdepth)
    css_and_js(head, body, css_files, js_files)
    perform_modules(head, body)


def recursive_clean(element):
    for key in element.attrib:
        if key.startswith('data-'):
            element.attrib.pop(key)
    for sub in element:
        recursive_clean(sub)


def cleaner(root: LyXobj):
    head, body = root[0], root[1]
    for sub in head.iter('meta'):
        if sub.attrib.get('name') != 'viewport':
            head.remove(sub)
    recursive_clean(body)
