from PyLyX.helper import *
from PyLyX.environments import Environment



def __line2toc(line: str):
    cmd = line.split()
    if len(cmd) > 3:
        raise Exception(f'invalid cmd: {line}')

    cmd += ['', '']
    cmd = cmd[:3]

    command, category, details = cmd
    command = command[len(BEGIN):]
    if details.startswith(USD) and details.endswith(USD):
        text, details = details + '\n', ''
    else:
        text = ''

    toc = Environment(command, category, text, details=details)
    if 0 <= toc.rank() <= 6:
        section = Environment('', '', details='')
        section.append(toc)
        toc.close()
        toc = section
    return toc


def __one_line(line: str, branch: list[Environment]):
    last = branch[-1]

    if line.startswith(BEGIN):
        new = __line2toc(line)
        while not new.can_be_nested_in(last):
            last.close()
            branch.pop()
            last = branch[-1]
        last.append(new)
        branch.append(new)

    elif line == f'{END}{last.command()}\n' and line[len(END):-1] in COMMANDS:
        last.close()
        if last.is_section():
            branch.pop()

    elif last.is_open():
        last.text += line

    else:  # i.e. last is close
        last.tail += line


def __reader(file):
    line = file.readline()
    while line != f'{BEGIN}{DOCUMENT}\n':
        line = file.readline()
    root = __line2toc(line)

    branch = [root]
    for line in file:
        __one_line(line, branch)

    return root


def load(full_path: str):
    with open(full_path, 'r', encoding='utf8') as file:
        root = __reader(file)
    return root
