from os.path import join
from PyLyX.data.data import RTL_LANGS, PACKAGE_PATH, TRANSLATE
from PyLyX.objects.LyXobj import LyXobj
from PyLyX.objects.Environment import Environment

MATHJAX = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js'
CSS_FOLDER = join(PACKAGE_PATH, 'lyx2xhtml\\css')
BASIC_RTL_CSS, BASIC_LTR_CSS = 'basic_rtl.css', 'basic_ltr.css'
SECTIONS = ('Part', 'Chapter', 'Section', 'Subsection', 'Subsubsection', 'Paragraph', 'Subparagraph')


def scan_head(head: Environment):
    dictionary = {}
    for e in head:
        lst = e.get('class').split(maxsplit=1)
        if len(lst) == 2:
            class_, value = lst
            if e.tag in {'language', 'secnumdepth', 'tocdepth', 'modules'}:
                if class_ in {'secnumdepth', 'tocdepth'}:
                    value = int(value)
                dictionary[class_] = value
    return dictionary


def perform_lang(root: Environment, head: Environment, lang: str):
    if lang in RTL_LANGS:
        root.set('lang', RTL_LANGS[lang])
        head.append(create_css(join(CSS_FOLDER, BASIC_RTL_CSS)))
    else:
        head.append(create_css(join(CSS_FOLDER, BASIC_LTR_CSS)))


def create_title(head: LyXobj, body: LyXobj):
    title = body.find('h1')
    if title is not None:
        while not title.text and len(title):
                title = title[0]
        head_title = LyXobj('title', text=title.text)
        head.append(head_title)


def create_css(path: str):
    attrib = {'rel': 'stylesheet', 'type': 'text/css', 'href': path}
    return LyXobj('link', attrib=attrib)


def create_script(source: str, async_=''):
    attrib = {'src': source}
    if async_:
        attrib['async'] = async_
    return LyXobj('script', attrib=attrib)


def mathjax():
    return create_script(MATHJAX, 'async')


def viewport():
    attrib = {'name': 'viewport', 'content': 'width=device-width'}
    return LyXobj('meta', attrib=attrib)


def css_and_js(head, body, css_files=(), js_files=()):
    for file in css_files:
        head.append(create_css(file))
    for file in js_files:
        body.append(create_script(file))


def prefixing(obj: LyXobj, prefix, sep=' '):
    pre_obj = LyXobj('span', text=prefix+sep, attrib={'class': 'label'})
    obj.text, pre_obj.tail = '', obj.text
    obj.insert(0, pre_obj)


def tocing(lst: LyXobj, obj: LyXobj, prefix):
    item = LyXobj('li')
    obj.set('id', obj.attrib['class'].split()[1] + '_' + prefix)
    link = LyXobj('a', attrib={'href': '#' + obj.get('id', '')}, text=prefix+' '+obj.text)
    item.append(link)
    lst.append(item)
    return item


def num_and_toc(toc: LyXobj, element, secnumdepth=-1, tocdepth=-1, prefix='', lang='english'):
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
                        prefixing(sec[0], new_prefix)
                    num_and_toc(new_toc, sec, secnumdepth, tocdepth, new_prefix, lang)


def perform_toc(element, title, toc):
    if element.get('class') == 'inset CommandInset toc':
        element.extend((title, toc))
