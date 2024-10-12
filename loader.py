from xml.etree.ElementTree import fromstring, tostring, Element, indent
from PyLyX import ENDS, is_known_object, DESIGNS
from PyLyX.LyXobj import LyXobj
from PyLyX.Environment import Environment, Container


############################################### MAIN ###############################################
def one_line(file, line: str, branch: list, unknowns: dict, index=None):
    # print([str(branch[i]) for i in range(len(branch))])
    # print(line[:-1])
    last = branch[-1]
    if type(index) is int:
        line = file[index]
    if last.is_category('Formula') and last.is_open() and not is_end(line):
        last.text += line

    elif line.startswith('\\'):
        command, category, details, text = extract_cmd(line)
        if is_end(line):
            perform_end(branch, command)
        elif command == 'deeper':
            perform_deeper(branch)
        else:
            perform_new_obj(branch, unknowns, command, category, details, text)
    elif line.startswith('<lyxtabular'):
        perform_table(branch, unknowns, file, line, index)

    elif last.is_open():
       lst = line[:-1].split(maxsplit=1)
       if 'required' in last.get_dict() and len(lst) == 2:
           result = perform_required(last, *lst)
       else:
           result = False
       if not result:
           last.text += line[:-1]
    else:
        last.tail += line[:-1]



def load(full_path: str):
    with open(full_path, 'r', encoding='utf8') as file:
        line = file.readline()

        while not line.startswith('\\lyxformat'):
            line = file.readline()
        fmt = line.split()[1]

        while line != f'\\begin_document\n':
            line = file.readline()
        cmd = extract_cmd(line)
        root = Environment(*cmd)
        root.set('data-lyxformat', fmt)

        while line != f'\\begin_header\n':
            line = file.readline()
        cmd = extract_cmd(line)
        head = Environment(*cmd)
        root.append(head)

        line = file.readline()
        while line != '\\end_header\n':
            head.text += line
            line = file.readline()
        head.close()

        branch = [root]
        unknowns = {}
        for line in file:
            one_line(file, line, branch, unknowns)

        if unknowns:
            print('unknown objects:', unknowns)

    return root


############################################### HELPERS ###############################################
def extract_cmd(line: str):
    cmd = line.split()
    if len(cmd) < 3:
        cmd += ['', '', 'is not cmd']
    command, category, details = cmd[:3]
    if command.startswith('\\'):
        command = command.replace('\\begin_', '', 1)
        command = command.replace('\\end_', '', 1)
        if not line.startswith('\\begin{align*}') and not line.startswith('\\end{align*}'):
            command = command.replace('\\', '', 1)
    else:
        raise Exception(f'invalid command: {line[:-1]}')
    if category == 'Formula' and details.startswith('$'):
        if line.endswith('$\n'):
            text = '$' + line.split('$')[-2] + '$'
        else:
            text = '$' + line.split('$')[-1]
        details = ''
    else:
        text = ''
    return command, category, details, text


def order_object(branch: list, obj):
    copy_branch = branch.copy()
    try:
        while not obj.can_be_nested_in(branch[-1]):
            branch[-1].close()
            branch.pop()
    except IndexError:
        raise Exception(f'an error occurred when ordering object {obj} in branch: {[str(_) for _ in copy_branch]}')
    branch[-1].append(obj)
    branch.append(obj)

    if type(obj) is Container:
        branch.append(obj[0])


def perform_new_obj(branch: list, unknowns: dict, command: str, category: str, details: str, text: str):
    if is_known_object(command, category, details):
        obj = Environment(command, category, details, text)
        if obj.is_section_title():
            obj = Container(obj)
        order_object(branch, obj)
    else:
        unknowns[command] = {category: {details: {}}}
        print(f'unknown object: {command}-{category}-{details}')
        obj = LyXobj('div', command, category, details, text)
        order_object(branch, obj)


def perform_end(branch: list, command: str):
    for i in range(-1, -len(branch)-1, -1):
        if branch[i].is_command(command):
            branch[i].close()
            tail = branch[len(branch)-i:]
            new_tail = []
            for _ in range(-i-1):
                branch[-1].close()
                branch.pop()
            if branch[-1].command() in DESIGNS:
                for item in tail:
                    if item.command() in DESIGNS and item.is_open():
                        new_tail.append(Environment(item.command(), item.category(), item.details()))
                if new_tail:
                    branch.pop()
                    branch.extend(new_tail)
            elif command == 'deeper':
                branch.pop()
                branch[-1].close()
            break


def perform_deeper(branch: list):
    deeper = Environment('deeper')
    obj = Container(branch[-1])
    obj.append(deeper)
    branch[-2].remove(branch[-1])
    branch[-2].append(obj)
    branch.pop()
    branch.append(obj)
    branch.append(deeper)


def perform_required(obj: Environment, first: str, second: str):
    lst = obj.get_dict().get('required', []) + obj.get_dict().get('optional', [])
    if first in lst:
        obj.set(first, second)
        return True
    else:
        return False


def is_end(line: str) -> bool:
    if line.startswith('\\'):
        if line.endswith('default\n'):
            return True
        for key in ENDS:
            for design in ENDS[key]:
                if line == f'\\{design} {ENDS[key][design]}\n':
                    return True
        return line.startswith('\\end_')

    return False


#################### tables ####################
def load_table_code(file, line, index=None):
    code = line
    counter = 1
    for line in file:
        if type(index) is int:
            index += 1
        if line.startswith('<features') or line.startswith('<column'):
            if not line.endswith('/>\n'):
                line = line.replace('>', '/>')
        code += line
        if line.startswith('<lyxtabular'):
            counter += 1
        elif line.startswith('</lyxtabular'):
            counter -= 1
            if not counter:
                break
    if type(file) is list and type(index) is int:
        new_lst = file[index+1:]
        file.clear()
        file.extend(new_lst)
    return code


def one_cell(cell: Element, unknowns: dict):
    new_cell = LyXobj(cell.tag, attrib=cell.attrib)
    text = cell.text
    for e in cell:
        indent(e, space='')
        text += tostring(e, encoding='unicode')
    branch = [new_cell]
    text = text.splitlines(keepends=True)
    index = 0
    for line in text:
        one_line(text, line, branch, unknowns, index)
        index += 1
    return new_cell


def table2lyxobj(table: Element, unknowns: dict):
    new_table = LyXobj(table.tag, attrib=table.attrib)
    for item in table:
        new_item = LyXobj(item.tag, attrib=item.attrib)
        new_table.append(new_item)
        for cell in item:
            new_cell = one_cell(cell, unknowns)
            new_item.append(new_cell)
    return new_table


def perform_table(branch: list, unknowns: dict, file, line, index):
    if type(file) is list and type(index) is int:
        new_lst = file[index + 1:]
        file.clear()
        file.extend(new_lst)
    code = load_table_code(file, line, index)
    table = fromstring(code)
    table = table2lyxobj(table, unknowns)
    branch[-1].append(table)
