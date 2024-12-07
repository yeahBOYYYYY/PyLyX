from os.path import join
from json import load
from PyLyX.data.data import PAR_SET, PACKAGE_PATH, TRANSLATE
from PyLyX.objects.LyXobj import LyXobj, DEFAULT_RANK
from PyLyX.objects.Environment import Environment, Container
from PyLyX.lyx2xhtml.helper import perform_table, perform_list, obj2text, correct_formula
from PyLyX.lyx2xhtml.general import scan_head, perform_lang, create_title, mathjax, viewport, css_and_js, num_and_toc, perform_toc

with open(join(PACKAGE_PATH, 'lyx2xhtml\\data\\tags.json'), 'r', encoding='utf8') as f:
    TAGS = load(f)
with open(join(PACKAGE_PATH, 'lyx2xhtml\\data\\tables.json'), 'r', encoding='utf8') as f:
    TABLES = load(f)


def create_dict(obj):
    if type(obj) is Environment and obj.is_in(TAGS):
        dictionary = TAGS[obj.command()][obj.category()][obj.details()]
    elif type(obj) is Environment and obj.tag in TABLES:
        dictionary = TABLES[obj.tag]
    elif type(obj) is Container:
        dictionary = {'tag': 'section'}
    elif (obj.is_command('layout') and not (obj.is_category('Plain') and obj.is_details('Layout'))) or obj.command() in PAR_SET:
        dictionary = {'tag': 'div'}
    else:
        dictionary = {'tag': 'span'}
    return dictionary


def perform_box(obj, old_attrib: dict, new_attrib: dict):
    style = []
    if 'framecolor' in old_attrib:
        if not obj.is_command('Frameless'):
            if old_attrib['framecolor'] != '"default"':
                style.append(f'border-color: {old_attrib.pop('framecolor')}')
    if 'backgroundcolor' in old_attrib:
        if old_attrib['backgroundcolor'] != '"none"':
            style.append(f'background-color: {old_attrib.pop('backgroundcolor')}')
    if style:
        style = '; '.join(style)
        new_attrib['style'] = style

    if 'width' in new_attrib:
        new_attrib['width'] = new_attrib['width'].replace('col%', '%')


def perform_cell(old_attrib: dict, new_attrib: dict):
    style = []
    for side in ('top', 'bottom', 'right', 'left'):
        value = old_attrib.pop(f'{side}line', None)
        if value == 'true':
            style.append(f'border-{side}: solid 1px')
    if style:
        style = '; '.join(style)
        new_attrib['style'] = style


def perform_include(obj: LyXobj):
    if 'data-filename' in obj.attrib:
        path = obj.get('data-filename')
        if path.endswith('.lyx'):
            from PyLyX import LyX
            root = LyX(path).load()
            root = convert(root)
            body = root[1]
            include_body = LyXobj('div', attrib={'class': 'include body'}, rank=-DEFAULT_RANK)
            obj.append(include_body)
            for element in body:
                include_body.append(element)


def create_attributes(obj, dictionary: dict, keep_data=False):
    old_attrib = obj.attrib.copy()
    new_attrib = {}

    if 'options' in dictionary:
        for key in dictionary['options']:
            if key in old_attrib:
                new_key, value = dictionary['options'][key], old_attrib.pop(key)
                new_attrib[new_key] = value
    if 'class' in old_attrib:
        new_attrib['class'] = old_attrib.pop('class')

    if obj.is_category('Box'):
        perform_box(obj, old_attrib, new_attrib)
    elif obj.tag == 'cell':
        perform_cell(old_attrib, new_attrib)
    elif obj.is_details('ref'):
        new_attrib['href'] = '#' + new_attrib['href']
    elif obj.is_category('other'):
        old_attrib['details'] = obj.details()
    elif obj.is_category('FormulaMacro'):
        lines = obj.text.splitlines()[1:]
        lines = '\n'.join(lines)
        old_attrib['lines'] = lines
    if keep_data:
        for key in old_attrib:
            new_attrib[f'data-{key}'] = old_attrib[key].replace('"', '')
    elif 'filename' in old_attrib:
        new_attrib['data-filename'] = old_attrib['filename'].replace('"', '')
    return new_attrib


def create_text(obj, new_attrib: dict):
    if obj.is_category('Formula'):
        return correct_formula(obj.text)
    elif obj.is_category('FormulaMacro'):
        macro = obj.text.splitlines()[0]
        return correct_formula(macro)
    elif 'text' in new_attrib:
        return new_attrib.pop('text')
    else:
        return obj.text


def one_obj(obj, keep_data=False):
    dictionary = create_dict(obj)
    attrib = create_attributes(obj, dictionary, keep_data)
    text = create_text(obj, attrib)
    new_obj = obj.copy()
    new_obj.open()
    for e in new_obj:
        e.open()
    new_obj.tag, new_obj.text, new_obj.attrib = dictionary['tag'], text, attrib
    if 'class' in new_obj.attrib and new_obj.attrib['class'].endswith('*'):
        new_obj.set('class', new_obj.get('class')[:-1] + '_')
    if new_obj.is_details('include'):
        perform_include(new_obj)
    return new_obj


def recursive_convert(obj, lang='english', toc=None, keep_data=False):
    if obj.is_command('lang'):
        lang = obj.category()
    new_obj = one_obj(obj, keep_data)
    is_first = True
    for child in obj:
        child = recursive_convert(child, lang, toc, keep_data)
        if child.is_section_title() and is_first:
            new_obj[0] = child
        else:
            new_obj.append(child)
        is_first = False
    perform_table(new_obj, lang)
    perform_list(new_obj)
    perform_toc(new_obj, *toc)
    obj2text(new_obj)
    return new_obj


def convert(root, css_files=(), js_files=(), keep_data=False):
    if len(root) == 2:
        info = scan_head(root[0])
        lang = info.get('language', 'english')
        if keep_data:
            head = recursive_convert(root[0])
            for e in head.iter():
                e.tag = 'meta'
        else:
            head = one_obj(root[0])
        head.extend((mathjax(), viewport()))
        perform_lang(root, head, lang)

        toc = LyXobj('ul')
        title_toc = LyXobj('h2', text=TRANSLATE['inset']['CommandInset']['toc'][lang])
        body = recursive_convert(root[1], lang, (title_toc, toc), keep_data)
        create_title(head, body)
        css_and_js(head, body, css_files, js_files)
        num_and_toc(toc, body, info.get('secnumdepth', -1), info.get('tocdepth', -1), '', lang)

        root = one_obj(root, keep_data)
        root.set('xmlns', 'http://www.w3.org/1999/xhtml')
        root.extend((head, body))
        return root
    else:
        raise Exception(f'root must contain 2 subelements exactly, not {len(root)}.')
