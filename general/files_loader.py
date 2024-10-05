from xml.etree.ElementTree import fromstring
from PyLyX.general.objects import LyxObj, Environment, Section, is_known_object
from PyLyX.general.tables_loader import lyxml2xhtml


def perform_required(obj, first: str, second: str):
    dictionary = obj.get_dict()
    if 'required' not in dictionary:
        return False
    elif first in dictionary['required']:
        key = dictionary['required'][first]
        if key == 'text':
            obj.text += second
        else:
            second = second.replace('"', '')
            obj.set(key, second)
        return True
    if 'more' in dictionary['required']:
        lst = dictionary['required']['more'].split()
        if first in lst:
            obj.set(f'data-{first}', second)
            return True

    return False


def extract_cmd(line: str):
    cmd = line.split()
    if len(cmd) < 3:
        cmd += ['', '', 'is not cmd']
    command, category, details = cmd[:3]
    if command.startswith('\\'):
        command = command.replace('\\begin_', '', 1)
        command = command.replace('\\end_', '', 1)
        command = command.replace('\\', '', 1)
    else:
        raise Exception(f'invalid command: {line[:-1]}')
    if details.startswith('$') and details.endswith('$'):
        text, details = details, ''
    else:
        text = ''
    return command, category, details, text


def correct_formula(formula: str):
    if formula.startswith('\\[') and formula.endswith('\\]'):
        return formula

    if formula.startswith('$'):
        formula = formula[1:]
    if formula.endswith('$'):
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
    while not obj.can_be_nested_in(branch[-1]):
        branch[-1].close()
        branch.pop()
    branch[-1].append(obj)
    branch.append(obj)

    if obj.is_formula():
        obj.text = correct_formula(obj.text)
    if obj.is_section():
        branch.append(obj[0])


def one_line(line: str, branch: list):
    # print(line)
    last = branch[-1]
    if line.startswith('\\'):
        command, category, details, text = extract_cmd(line)
        if line.startswith('\\end_') or line.endswith('default\n'):
            for i in range(-1, -len(branch), -1):
                if branch[i].end() and line == branch[i].end():
                    branch[i].close()
                    branch, tail = branch[:len(branch)+i+1], branch[len(branch)+i+1:]
                    for obj in tail:
                        obj.close()
                break
        elif is_known_object(command, category, details):
            obj = Environment(command, category, details, text)
            if obj.is_section_title():
                obj = Section(obj)
            order_object(branch, obj)
        elif last.is_formula():
            last.text += line[:-1]
        else:
            # print(f'unknown object: {line[:-1]}')
            obj = LyxObj('div', command, category, details, text)
            obj.close()
            order_object(branch, obj)
    elif last.is_open():
       lst = line[:-1].split(maxsplit=1)
       if len(lst) != 2 or not perform_required(last, *lst):
           last.text += line[:-1]
    else:
        last.tail += line[:-1]


def load_table_code(lines):
    line = ''
    for line in lines:
        if line.startswith('<lyxtabular'):
            break

    code = line
    counter = 0
    for line in lines:
        if line.startswith('<features') or line.startswith('<column'):
            if not line.endswith(f'/>\n'):
                line = line.replace('>', ' />')

        code += line

        if line.startswith('<lyxtabular'):
            counter += 1
        elif line == f'</lyxtabular>\n':
            counter -= 1
            if not counter:
                break

    return code


def scan(lines, branch):
    for line in lines:
        one_line(line, branch)
        if branch[-1].is_table_inset():
            code = load_table_code(lines)
            table = lyxml2xhtml(fromstring(code))
            branch[-1].append(table)


def load(full_path: str):
    with open(full_path, 'r', encoding='utf8') as file:
        line = file.readline()
        while not line.startswith(f'\\{'lyxformat'}'):
            line = file.readline()
        cmd = extract_cmd(line)
        lyxformat = LyxObj('meta')
        lyxformat.attrib = {'name': 'lyxformat', 'content': cmd[1]}

        while line != f'\\begin_document\n':
            line = file.readline()
        cmd = extract_cmd(line)
        root = Environment(*cmd)

        branch = [root]
        scan(file, branch)

        head = root[0]
        head.open()
        head.append(lyxformat)
        head.close()
    return root
