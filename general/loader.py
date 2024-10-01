from PyLyX.general.helper import *
from PyLyX.general.objects import Environment, Section


def extract_cmd(line: str):
    cmd = line.split()
    if len(cmd) < 3:
        cmd += ['', '', 'is not cmd']
    command, category, details = cmd[:3]
    command = command[command.find('_') + 1:]
    if details.startswith(USD) and details.endswith(USD):
        text, details = details + '\n', ''
    else:
        text = ''
    return command, category, details, text


def one_line(line: str, branch: list):
    last = branch[-1]
    command, category, details, text = extract_cmd(line)

    if line.startswith(BEGIN) and command in OBJECTS and category in OBJECTS[command] and details in OBJECTS[command][category]:
        new = Environment(command, category, details, text)
        if type(new) is Environment and new.is_section_title():
            new = Section(new)
        while not new.can_be_nested_in(last):
            last.close()
            branch.pop()
            last = branch[-1]
        last.append(new)
        branch.append(new)
        if type(new) is Section:
            branch.append(new[0])
    elif line.startswith(BEGIN):
        raise Exception(f'unknown command: {line[:-1]}.')

    elif line.startswith(END) and command in OBJECTS:
        if command == 'index':
            last.tail += line
        else:
            while last.is_close():
                branch.pop()
                last = branch[-1]
            if line == f'{END}{last.command()}\n':
                last.close()
            elif line == f'{END}{BODY}\n':
                while last.command() != DOCUMENT:
                    last.close()
                    branch.pop()
                    last = branch[-1]
            else:
                raise Exception(f'invalid LyX document: last object is {last}, but current line is "{line[:-1]}".')

    elif last.is_open():
        last.text += line
    else:  # i.e. last is close
        last.tail += line


def load(full_path: str):
    with open(full_path, 'r', encoding='utf8') as file:
        line = file.readline()
        while line != f'{BEGIN}{DOCUMENT}\n':
            line = file.readline()
        cmd = extract_cmd(line)
        root = Environment(*cmd)
        branch = [root]
        for line in file:
            one_line(line, branch)
    return root
