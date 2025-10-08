"""
Convert LyX keybinding files to readable LyX documents.

This module parses LyX .bind files (keyboard shortcut configurations)
and generates a formatted LyX document with tables showing:
- Keyboard shortcuts
- Associated commands
- Command outputs/descriptions

Usage:
    python bind2lyx.py [bind_file] [output_file]
"""

from os import remove
from os.path import split, splitext, exists, join
from sys import argv
from json import load
from PyLyX import LyX
from PyLyX.data.data import USER, USER_DIR, SYS_DIR, PACKAGE_PATH
from PyLyX.objects.Environment import Environment, Container
from tables_creator import create_table
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
    """
    Translate LyX shortcut notation to human-readable format.
    
    Converts LyX's internal shortcut format to standard notation:
    - C- → Ctrl+
    - M- → Alt+
    - S- → Shift+
    Also handles special keys and shifted characters.
    
    :param code: LyX shortcut code (e.g., 'C-S-x')
    :return: Human-readable shortcut (e.g., 'Ctrl+Shift+X')
    """
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
    """
    Convert LyX command to displayable format.
    
    Transforms LyX command strings into readable/renderable formats:
    - Simplifies complex command sequences
    - Converts math-insert commands to actual formulas
    - Converts math-delim commands to delimiter pairs
    
    :param code: LyX command string
    :return: Formatted command string or Environment object for rendering
    """
    if code.startswith('command-sequence'):
        code = 'command-sequence...'
    elif code.startswith('command-alternatives'):
        code = 'command-alternative...'
    elif code.startswith('paragraph-params'):
        code = 'paragraph-params...'
    elif code.startswith('math-insert '):
        code = code[len('math-insert '):]
        code = code.replace('\\\\', '\\')
        code = Environment('inset', 'Formula', text=f'${code}$')
    elif code.startswith('math-delim '):
        code = code[len('math-delim '):]
        code.replace('langle', '<')
        code.replace('rangle', '>')
        code = f'\\left{code[0]} \\right{code[-1]}'
        code = Environment('inset', 'Formula', text=f'${code}$')

    return code


def translate_table(table: list[list]):
    """
    Translate all shortcuts and commands in a table.
    
    Applies translate_shortcut and command2lyx to each row.
    
    :param table: List of [shortcut, command] pairs
    """
    for i in range(len(table)):
        table[i][0] = translate_shortcut(table[i][0])
        table[i][1] = command2lyx(table[i][1])


def design_table(table: list[list]):
    """
    Format table with headers and row numbers.
    
    Adds a header row and prepends row numbers to each entry.
    Also adds an empty explanations column.
    
    :param table: List of data rows to format
    """
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
        table = create_table(table)
        father = Environment('inset', 'Tabular')
        father.append(table)
        align = Environment('align', 'center')
        align.append(father)
        standard = Environment('layout', 'Standard')
        standard.append(align)
        env = Environment('layout', LAYOUTS[depth + 1], text=title)
        section = Container(env)
        section.append(standard)
        tables[i] = section

    name = splitext(split(full_path)[1])[0]
    if depth >= 2:
        name = name.upper()
    env = Environment('layout', LAYOUTS[depth], text=name)
    section = Container(env)
    for t in tables:
        section.append(t)
    return section, files


def recursive_write(path: str, files: list, result: LyX, depth=2):
    for name in files:
        if name.count('\\') and name.count('/'):
            obj, files0 = one_file(name, depth)
        else:
            obj, files0 = one_file(join(path, name), depth)
        result.append(obj)
        recursive_write(path, files0, result, depth + 1)


def write_all_files(full_path: str, final_path: str):
    if exists(final_path):
        remove(final_path)
    if exists(final_path + '~'):
        remove(final_path + '~')

    obj, files = one_file(full_path)
    files.append(join(PERSONAL_PATH, 'user.bind'))
    result = LyX(join(PACKAGE_PATH, r'shortcuts\data\template.lyx'), writeable=False)
    result.append(obj)
    recursive_write(split(full_path)[0], files, result)
    result.save_as(final_path)


DEFAULT_PATH = join(SYS_DIR, 'bind')
DEFAULT_NAME = 'cua.bind'
PERSONAL_PATH = join(USER_DIR, 'bind')


def main():
    path, name = DEFAULT_PATH, DEFAULT_NAME
    final_path, final_name = f'{USER}\\Downloads', 'table_of_shortcuts.lyx'
    if len(argv) == 1:
        pass
    elif len(argv) == 2:
        path, name = split(argv[1])
    elif len(argv) == 3:
        final_path, final_name = split(argv[2])
    else:
        print(f'Too many inputs, I will ignore any input in {argv[4:]}.')

    if path == DEFAULT_PATH and exists(join(PERSONAL_PATH, DEFAULT_NAME)):
        print('Note: files in the user directory take precedence over files in the system directory.')
        path, name = PERSONAL_PATH, DEFAULT_NAME

    path = join(path, name)
    final_path = join(final_path, final_name)
    write_all_files(path, final_path)

    print(f'Mission complete: your shortcuts lyx file can be found in: {final_path}')


if __name__ == '__main__':
    main()
