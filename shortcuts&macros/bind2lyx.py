from os import remove
from sys import argv
from PyLyX.general.lyx import LyX
from PyLyX.general.objects import Environment, Section
from PyLyX.general.helper import *
from compare_bind import scan_file


with open('data\\shifted.json', 'r') as f:
    SHIFTED_DICT = load(f)
with open('data\\keys.json', 'r') as f:
    KEYS_DICT = load(f)

LAYOUTS = {0: 'Part',
           1: 'Chapter',
           2: 'Section',
           3: 'Subsection',
           4: 'Subsubsection',
           5: 'Paragraph',
           6: 'Subparagraph',
           7: 'Standard'}


def translate_shortcut(code):
    code = code.replace('C-', 'Ctrl+')
    code = code.replace('M-', 'Alt+')
    code = code.replace('S-', 'Shift+')
    for key in KEYS_DICT:
        code = code.replace(key, KEYS_DICT[key])
    code = code.replace('\\back/', '\\backslash')
    for key in SHIFTED_DICT:
        code = code.replace('Shift+' + key, 'Shift+' + SHIFTED_DICT[key])
    return code


def command2lyx(code: str):
    if code.startswith('command-sequence'):
        code = 'command-sequence...'
    elif code.startswith('command-alternatives'):
        code = 'command-alternative...'
    elif code.startswith('paragraph-params'):
        code = 'paragraph-params...'
    elif code.startswith('math-insert '):
        code = code[len('math-insert '):]
        code = code.replace('\\\\', '\\')
        code = Environment(INSET, FORMULA, text=f' \\({code}\\)')
    elif code.startswith('math-delim '):
        code = code[len('math-delim '):]
        code.replace('langle', '<')
        code.replace('rangle', '>')
        code = f'\\left{code[0]} \\right{code[-1]}'
        code = Environment(INSET, FORMULA, text=f' \\({code}\\)')

    return code


def translate_table(table: list[list]):
    for i in range(len(table)):
        table[i][0] = translate_shortcut(table[i][0])
        table[i][1] = command2lyx(table[i][1])


def design_table(table: list[list]):
    table.insert(0, ['', 'Shortcut', 'Output', 'Explanations'])
    for i in range(1, len(table)):
        table[i].insert(0, str(i))
        table[i].append('')


def one_file(full_path: str, depth=2):
    tables, canceled, files = scan_file(full_path)

    if canceled:
        canceled_table = ['CANCELED', canceled]
        tables.append(canceled_table)

    for i in range(len(tables)):
        title, table = tables[i]
        translate_table(table)
        design_table(table)
        table = table2lyx(table)
        table = Environment(INSET, TABLE, text=table)
        standard = Environment(LAYOUT, STANDARD)
        standard.append(table)
        env = Environment(LAYOUT, LAYOUTS[depth + 1], text=title)
        section = Section(env)
        section.append(standard)
        tables[i] = section

    name = splitext(split(full_path)[1])[0]
    if depth >= 2:
        name = name.upper()
    env = Environment(LAYOUT, LAYOUTS[depth], text=name)
    section = Section(env)
    for t in tables:
        section.append(t)
    return section, files


def recursive_write(path: str, files: list, result: LyX, depth=2):
    for name in files:
        if name.count('\\') and name.count('/'):
            obj, files0 = one_file(name, depth)
        else:
            obj, files0 = one_file(join(path, name), depth)
        result.write(obj)
        recursive_write(path, files0, result, depth + 1)


def write_all_files(full_path: str, final_path: str):
    if exists(final_path):
        remove(final_path)
    if exists(final_path + '~'):
        remove(final_path + '~')

    obj, files = one_file(full_path)
    files.append(join(PERSONAL_PATH, PERSONAL_NAME))
    result = LyX(final_path)
    result.write(obj)
    recursive_write(split(full_path)[0], files, result)


DEFAULT_PATH = join(SYS_DIR, 'bind')
DEFAULT_NAME = 'cua.bind'
PERSONAL_PATH = join(USER_DIR, 'bind')
PERSONAL_NAME = 'user.bind'
FINAL_PATH = f'{USER}\\Downloads'
FINAL_NAME = 'table_of_shortcuts.lyx'
COMPLETE_MESSAGE = 'Mission complete: your shortcuts lyx file can be found in '
NOTATION = 'Note: files in the user directory take precedence over files in the system directory.'


def main():
    path, name = DEFAULT_PATH, DEFAULT_NAME
    final_path, final_name = FINAL_PATH, FINAL_NAME
    if len(argv) == 1:
        pass
    elif len(argv) == 2:
        path, name = split(argv[1])
    elif len(argv) == 3:
        final_path, final_name = split(argv[2])
    else:
        print(f'Too many inputs, I will ignore any input in {argv[4:]}.')

    if path == DEFAULT_PATH and exists(join(PERSONAL_PATH, DEFAULT_NAME)):
        path, name = PERSONAL_PATH, DEFAULT_NAME
        print(NOTATION)

    path = join(path, name)
    final_path = join(final_path, final_name)
    write_all_files(path, final_path)
    print(COMPLETE_MESSAGE + final_path)


if __name__ == '__main__':
    main()
