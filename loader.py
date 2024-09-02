from json import dumps
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


def perform_env(line: str, branch: list[Object], unknown: dict):
    last = branch[-1]
    command, category, details, text = extract_cmd(line)
    if line.startswith(BEGIN) and command in ENVIRONMENTS:
        new = Environment(command, category, details, text)
        if new.is_section_title():
            new = Section(new)
        while not new.can_be_nested_in(last):
            last.close()
            branch.pop()
            last = branch[-1]
        last.append(new)
        branch.append(new)
    elif line.startswith(END) and command in ENVIRONMENTS:
        while last.is_close():
            branch.pop()
            last = branch[-1]
        if line == f'{END}{last.command()}\n':
            last.close()
        elif ENVIRONMENTS[command] != 'end_only':
            raise Exception(f'invalid LyX Document: last object opened with {BEGIN}{last.command()}, but current line is {line}.')
    elif command in KEY_WORDS:
        design = Design(command, category, details)
        last.append(design)
    else:
        unknown[command] = {category: {details: {}}}
        print(f'unknown command: {line}')
        if last.is_open():
            last.text += line
        else:  # i.e. last is close
            last.tail += line


def one_line(line: str, branch: list[Object], unknown: dict):
    last = branch[-1]

    if line.startswith('\\'):
        if last.category() == FORMULA and last.is_open():
            last.text += line
        else:
            perform_env(line, branch, unknown)
    elif last.is_open():
        last.text += line
    else:  # i.e. last is close
        last.tail += line


def create_primary_env(file, command: str) -> Environment:
    line = file.readline()
    while line != f'{BEGIN}{command}\n':
        line = file.readline()
    cmd = extract_cmd(line)
    env = Environment(*cmd)
    return env


def create_header(file):
    header = create_primary_env(file, HEADER)
    branch = [header]
    line = file.readline()
    while line != f'{END}{HEADER}\n':
        last = branch[-1]
        if line.startswith(BEGIN) or line.startswith(END):
            perform_env(line, branch, {})
        elif last.is_open():
                last.text += line
        else:  # i.e. last is close
            last.tail += line
        line = file.readline()
    return header


def load(full_path: str):
    with open(full_path, 'r', encoding='utf8') as file:
        root = create_primary_env(file, DOCUMENT)
        header = create_header(file)
        root.append(header)
        branch = [root]
        unknown = {}
        for line in file:
            one_line(line, branch, unknown)
    if unknown:
        string = dumps(unknown, indent=0)
        with open(join(DOWNLOADS_DIR, 'unknown_commands.json'), 'w', encoding='utf8') as file:
            file.write(string)
    return root
