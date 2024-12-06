from os.path import join
from PyLyX.data.data import PACKAGE_PATH
from PyLyX.objects.LyXobj import LyXobj
from PyLyX.lyx2xhtml.helper import perform_tables, perform_lists, obj2text, rec_num_and_toc, perform_toc

MATHJAX = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js'
CSS_FOLDER = join(PACKAGE_PATH, 'lyx2xhtml\\css')
RTL_LANGS = {'hebrew': 'He-IL'}
BASIC_LTR_CSS = 'basic_ltr.css'
BASIC_RTL_CSS = 'basic_rtl.css'


def viewport():
    attrib = {'name': 'viewport', 'content': 'width=device-width'}
    return LyXobj('meta', attrib=attrib)


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


def css_and_js(head, body, css_files=(), js_files=()):
    for file in css_files:
        head.append(create_css(file))
    for file in js_files:
        body.append(create_script(file))


def scan_head(head: LyXobj, keep_data=False):
    dictionary = {}
    for e in head.findall('meta'):
        class_ = e.get('class')
        value = e.get('data-value')
        if class_ in {'language', 'secnumdepth', 'tocdepth', 'modules'}:
            if class_ in {'secnumdepth', 'tocdepth'}:
                value = int(value)
            dictionary[class_] = value
        elif not keep_data:
            head.remove(e)
    return dictionary


def perform_lang(root, head, lang):
    if lang in RTL_LANGS:
        root.set('lang', RTL_LANGS[lang])
        head.append(create_css(join(CSS_FOLDER, BASIC_RTL_CSS)))
    else:
        head.append(create_css(join(CSS_FOLDER, BASIC_LTR_CSS)))
    return lang


def num_and_toc(body, secnumdepth, tocdepth, lang):
    toc = LyXobj('ul')
    rec_num_and_toc(toc, body, secnumdepth, tocdepth, '', lang)
    perform_toc(body, toc, lang)


def perform_modules(modules, body):
    # for m in modules:
    #     path = join(PACKAGE_PATH, 'modules', f'{m}.py')
    #     if exists(path):
    #         pass  # todo: perform module
    #     else:
    #         print(f'unknown module: {m}.')
    pass


def design(root, css_files=(), js_files=(), keep_data=False):
    root.set('xmlns', 'http://www.w3.org/1999/xhtml')
    head, body = root[0], root[1]
    create_title(head, body)

    perform_tables(body)
    perform_lists(body)
    obj2text(body)

    info = scan_head(head, keep_data)
    perform_lang(root, head, info.get('language', 'english'))
    num_and_toc(body, info.get('secnumdepth', -1), info.get('tocdepth', -1), info.get('language', 'english'))
    perform_modules(head, body)
    css_and_js(head, body, css_files, js_files)
    head.extend((create_script(MATHJAX, 'async'), viewport()))