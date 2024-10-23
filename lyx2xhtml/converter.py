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
    elif type(obj) is Container or obj.is_command('deeper'):
        dictionary = {'tag': 'section'}
    elif type(obj) is LyXobj and obj.tag in TABLES:
        dictionary = TABLES[obj.tag]
    else:
        dictionary = {}
    if (obj.is_command('layout') and not (obj.is_category('Plain') and obj.is_details('Layout'))) or \
            obj.command() in PAR_SET:
        dictionary.setdefault('tag', 'div')
    else:
        dictionary.setdefault('tag', 'span')
    return dictionary


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
    if obj.tag == 'cell':
        style = []
        for side in ('top', 'bottom', 'right', 'left'):
            value = old_attrib.pop(f'{side}line', None)
            if value == 'true':
                style.append(f'border-{side}: solid 1px')
        if style:
            style = '; '.join(style)
            new_attrib['style'] = style

    for key in old_attrib:
        new_attrib[f'data-{key}'] = old_attrib[key]

    return new_attrib


def create_text(obj, new_attrib: dict):
    if obj.is_command('header'):  # todo: head will be create better in the future
        return ''
    elif obj.is_category('Formula'):
        return correct_formula(obj.text)
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
    if 'class' in new_obj.attrib:
        new_obj.set('class', new_obj.get('class').replace('*', '_'))
    return new_obj


def recursive_convert(obj):
    new_obj = one_obj(obj)
    for child in obj:
        child = recursive_convert(child)
        new_obj.append(child)
    return new_obj


def convert(root, css_path=BASIC_CSS):
    root = recursive_convert(root)
    root.set('xmlns', 'http://www.w3.org/1999/xhtml')
    if len(root) == 2:
        order_document(*root, css_path)
        return root
    else:
        raise Exception(f'root must contain 2 subelements exactly, not {len(root)}.')
