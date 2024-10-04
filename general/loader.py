from xml.etree.ElementTree import Element
from PyLyX.general.helper import *
from PyLyX.general.objects import Environment, Section, LyxObj
from PyLyX.general.tables import code2xml, xml2xhtml


def perform_required(obj, first: str, second: str):
    require = 'require'
    more = 'more'
    dictionary = OBJECTS[obj.command()][obj.category()][obj.details()]
    if require not in dictionary:
        return False
    elif first in dictionary[require]:
        key = dictionary[require][first]
        if key == TEXT:
            obj.text += second
        else:
            obj.set(key, second)
        return True
    elif more in dictionary[require]:
        lst = dictionary[require][more].split()
        if first in lst:
            obj.set(f'data-{first}', second)
            return True

    return False


def load_table(file, line):
    code = [line[:-1]]
    for line in file:
        if line.startswith(f'<{FEATURES}') or line.startswith(f'<{COLUMN}'):
            if not line.endswith(f'/>\n'):
                line = line.replace('>', ' />')
        code.append(line[:-1])
        if line == f'</{TABLE_TAG}>\n':
            break
    return code


def extract_cmd(line: str):
    cmd = line.split()
    if len(cmd) < 3:
        cmd += ['', '', 'is not cmd']
    command, category, details = cmd[:3]
    if command.startswith('\\'):
        command = command[1:]
    else:
        raise Exception(f'invalid command: {line[:-1]}')
    command = command[command.find('_') + 1:]
    if details.startswith(USD) and details.endswith(USD):
        text, details = details, ''
    else:
        text = ''
    return command, category, details, text


def is_known_object(command: str, category: str, details: str):
    return command in OBJECTS and category in OBJECTS[command] and details in OBJECTS[command][category]


def correct_formula(formula: str):
    if formula.startswith('\\[') and formula.endswith('\\]'):
        return formula

    if formula.startswith(USD):
        formula = formula[1:]
    if formula.endswith(USD):
        formula = formula[:-1]
    if formula.startswith('\\('):
        formula = formula[2:]
    if formula.endswith('\\)'):
        formula = formula[:-2]

    if formula.startswith('\\['):
        return formula +'\\]'
    if formula.endswith('\\]'):
        return '\\[' + formula

    return '\\(' + formula + '\\)'


def order_object(branch: list, obj):
    while branch and not obj.can_be_nested_in(branch[-1]):
        branch[-1].close()
        branch.pop()
    if branch:
        branch[-1].append(obj)
    branch.append(obj)
    if type(obj) is Section:
        branch.append(obj[0])


def one_line(file, line: str, branch: list):
    last = branch[-1]
    if line.startswith('\\'):
        command, category, details, text = extract_cmd(line)
        if is_known_object(command, category, details):
            obj = Environment(command, category, details, text)
            if obj.is_section_title():
                obj = Section(obj)
            order_object(branch, obj)
        elif last.is_formula():
            last.text += line[:-1]
        else:
            if last.end() and line == last.end():
                last.close()
            else:
                print(f'unknown object: {line[:-1]}')
                obj = LyxObj(command, category, details, text)
                obj.close()
                order_object(branch, obj)

    elif line.startswith(f'<{TABLE_TAG}') and last:
        code = load_table(file, line)
        xml = code2xml(code)
        xml2xhtml(xml, last)
    elif branch and branch[-1].is_environment():
        last = branch[-1]
        if last.is_open():
           lst = line.split()
           if not len(lst) == 2 or not perform_required(last, *lst):
               last.text += line[:-1]
        else:
            last.tail += line[:-1]

    return branch


def load(full_path: str):
    with open(full_path, 'r', encoding='utf8') as file:
        line = file.readline()
        while not line.startswith(f'\\{LYXFORMAT}'):
            line = file.readline()
        cmd = extract_cmd(line)
        lyxformat = Element(META, {'name': LYXFORMAT, 'content': cmd[1]})

        while line != f'{BEGIN}{DOCUMENT}\n':
            line = file.readline()
        cmd = extract_cmd(line)
        root = Environment(*cmd)

        branch = [root]
        for line in file:
            branch = one_line(file, line, branch)

        head = root[0]
        head.append(lyxformat)
    return root
