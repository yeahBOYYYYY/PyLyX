from PyLyX import PAR_SET
from PyLyX.Environment import Environment, Container
from PyLyX.lyx2xhtml.helper import *

with open(join(PACKAGE_PATH, 'lyx2xhtml\\data\\tags.json'), 'r', encoding='utf8') as f:
    TAGS = load(f)
with open(join(PACKAGE_PATH, 'lyx2xhtml\\data\\tables.json'), 'r', encoding='utf8') as f:
    TABLES = load(f)


def create_dict(obj):
    if type(obj) is Environment and obj.is_in(TAGS):
        dictionary = TAGS[obj.command()][obj.category()][obj.details()]
    elif type(obj) is Container:
        dictionary = {'tag': 'section'}
    elif type(obj) is LyXobj and obj.tag in TABLES:
        dictionary = TABLES[obj.tag]
    else:
        dictionary = {}

    if obj.is_command('layout') and not (obj.is_category('Plain') and obj.is_details('Layout')):
        tag = 'div'
    elif obj.command() in PAR_SET:
        tag = 'div'
    else:
        tag = 'span'
    dictionary.setdefault('tag', tag)
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


def create_attributes(obj, dictionary: dict):
    old_attrib = obj.attrib.copy()
    new_attrib = {}

    if 'options' in dictionary:
        for key in dictionary['options']:
            if key in old_attrib:
                new_key, value = dictionary['options'][key], old_attrib.pop(key).replace('"', '')  # todo: official func instead repkace
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
    for key in old_attrib:
        new_attrib[f'data-{key}'] = old_attrib[key].replace('"', '')

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


def one_obj(obj):
    dictionary = create_dict(obj)
    attrib = create_attributes(obj, dictionary)
    text = create_text(obj, attrib)
    properties = obj.command(), obj.category(), obj.details()
    new_obj = LyXobj(dictionary['tag'], *properties, text, obj.tail, attrib)
    if 'class' in new_obj.attrib and new_obj.attrib['class'].endswith('*'):
        new_obj.set('class', new_obj.get('class')[:-1] + '_')
    return new_obj


def recursive_convert(obj):
    new_obj = one_obj(obj)
    for child in obj:
        child = recursive_convert(child)
        if new_obj.tag in {'head', 'meta'}:
            child.tag = 'meta'
        new_obj.append(child)
    return new_obj


def convert(root, css_files=(BASIC_CSS, ), css_folder=CSS_FOLDER, js_files=(NUM_TOC, ), js_folder=JS_FOLDER):
    root = recursive_convert(root)
    root.set('xmlns', 'http://www.w3.org/1999/xhtml')
    if len(root) == 2:
        order_document(*root, css_files, css_folder, js_files, js_folder)
        return root
    else:
        raise Exception(f'root must contain 2 subelements exactly, not {len(root)}.')
