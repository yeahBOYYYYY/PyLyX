from os import remove
from sys import argv
from PyLyX.lyx import LYX
from PyLyX.toc import TOC
from PyLyX.helper import *
from compare_bind import scan_file


with open('data\\shifted.json', 'r') as f:
    SHIFTED_DICT = load(f)
with open('data\\keys.json', 'r') as f:
    KEYS_DICT = load(f)
with open('data\\layouts.json', 'r') as f:
    LAYOUTS = load(f)


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
        code = create_inset(FORMULA, f' ${code}$')
    elif code.startswith('math-delim '):
        code = code[len('math-delim '):]
        code.replace('langle', '<')
        code.replace('rangle', '>')
        code = f'\\left{code[0]} \\right{code[-1]}'
        code = create_inset(FORMULA, f' ${code}$')

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

    for t in tables:
        translate_table(t[1])
        design_table(t[1])
        t[1] = [TOC(STANDARD, t[1], [])]
        layout = CATEGORIES[str(depth + 1)]
        t.insert(0, layout)

    name = splitext(split(full_path)[1])[0]
    if depth >= 2:
        name = name.upper()
    layout = CATEGORIES[str(depth)]
    toc = TOC(layout, name, tables)
    return toc, files


def recursive_write(path: str, files: list, result: LYX, depth=2):
    for name in files:
        if name.count('\\') and name.count('/'):
            toc, files0 = one_file(name, depth)
        else:
            toc, files0 = one_file(join(path, name), depth)
        result.write(toc)
        recursive_write(path, files0, result, depth + 1)


def write_all_files(full_path: str, final_path: str):
    if exists(final_path):
        remove(final_path)
    if exists(final_path + '~'):
        remove(final_path + '~')

    toc, files = one_file(full_path)
    files.append(join(PERSONAL_PATH, PERSONAL_NAME))
    result = LYX(final_path, toc)
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
