from xml.etree.ElementTree import Element
from PyLyX.helper import *
from PyLyX.lyx import load, TOC

SECTION, SPAN, CLASS = 'section', 'span', 'class'

HREF, REF, LABEL, ID, NAME, TARGET = 'href', 'ref', 'label', 'id', 'name', 'target'
SPECIAL_CHARS = {'"': '&quot;', '&': '&amp;', "'": '&apos;', '<': '&lt;', '>': '&gt;'}
COMMAND_INSET = 'CommandInset'


def replace_underscore(text: str):
    text = text.replace(' ', '_')
    text = text.replace('.', '_')
    return text


def chars2xml(text: str):
    for char in SPECIAL_CHARS:
        text = text.replace(char, SPECIAL_CHARS[char])
    return text


def perform_command(element: Element, command: str, details: list[str]):
    attributes = {}
    for line in details:
        key, value = line.split()
        attributes[key] = value

    if command == HREF:
        element.attrib[command] = attributes.get(TARGET)
        element.text = attributes.get(NAME)
    elif command == REF:
        target = attributes.get(NAME)
        target = replace_underscore(target)
        element.attrib[HREF] = '#' + target
    elif command == LABEL:
        id_ = attributes.get(NAME)
        id_ = replace_underscore(id_)
        element.attrib[ID] = id_
    else:
        print(f'unknown command: {command}')
        return None
    return element


def create_element(cmd: list[str], text=''):
    command, class_ = cmd[0], cmd[1]
    text = text.split('\n')

    if command in COMMAND_DICT and class_ in COMMAND_DICT[command]:
        element = Element(COMMAND_DICT[command][class_])
    else:
        print(f'unknown command: {command}, {class_}')
        return Element('unknown')

    if class_ == COMMAND_INSET:
        perform_command(element, cmd[3], text)
    else:
        element.text = ''.join(text)
        if class_ == FORMULA:
            if len(cmd) != 2:
                element.text = '\\(' + cmd[2][1:-1] + '\\)'
            elif not element.text.startswith('\\['):
                element.text = '\\[' + element.text + '\\]'

    return element


def one_obj(file, cmd: list[str], father: Element):
    start = cmd[0]
    text, line = create_text(file)
    element = create_element(cmd, text)
    father.append(element)

    cmd = line.split()
    if cmd[0] == COMMANDS[start]:
        line = file.readline()
        if not line.startswith('\\'):
            tail, line = create_text(file, line)
            element.tail = tail
        cmd = line.split()
        return element, cmd
    else:
        element, cmd = one_obj(file, cmd, element)
        return element, cmd


def convert_text(lines: str):
    return ''


def one_toc(toc: TOC):
    lines = toc.text().split('\n')
    html_code = ''
    if toc.category() in CATEGORIES:
        for line in lines:
            if line == '\\backslash':
                html_code += '\\'
            elif line.startswith('\\'):
                pass
            else:
                html_code += line
    elif toc.category() in INSETS:
    return html_code


def converter(full_path: str, final_path: str):
    root = load(full_path)
    with open(final_path, 'x', encoding='utf8') as file:
        for toc in root:
            code = one_toc(toc)
            file.write(code)
