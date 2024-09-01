from PyLyX.helper import *
from PyLyX.environments import Environment, Section, Design, Object


def extract_cmd(line: str):
    cmd = line.split()
    if len(cmd) > 3:
        raise Exception(f'invalid cmd: {line}')

    cmd += ['', '']
    command, category, details = cmd[:3]
    command = command[command.find('_')+1:]
    if details.startswith(USD) and details.endswith(USD):
        text, details = details + '\n', ''
    else:
        text = ''
    return command, category, details, text


def one_line(line: str, branch: list[Object]):
    last = branch[-1]

    if line.startswith('\\'):
        command, category, details, text = extract_cmd(line)

        if line.startswith(BEGIN) and command in ENVIRONMENTS:
            new = Environment(command, category, details, text)
            if new.is_section_title():
                new = Section(new)
            while not new.can_be_nested_in(last):
                last.close()
                branch.pop()
                last = branch[-1]
            if new.is_section_title():
                new = Section(new)
            last.append(new)
            branch.append(new)

        elif type(last) is Environment and line == f'{END}{last.command()}\n' and command in ENVIRONMENTS:
            last.close()

        elif command in KEY_WORDS:
            design = Design(command, category, details)
            last.append(design)

        else:
            print(f'unknown command: {line}')

    elif last.is_open():
        last.text += line
    else:  # i.e. last is close
        last.tail += line


def reader(file):
    line = file.readline()
    while line != f'{BEGIN}{DOCUMENT}\n':
        line = file.readline()
    cmd = extract_cmd(line)
    root = Environment(*cmd)

    branch = [root]
    for line in file:
        one_line(line, branch)

    return root


def load(full_path: str):
    with open(full_path, 'r', encoding='utf8') as file:
        root = reader(file)
    return root
