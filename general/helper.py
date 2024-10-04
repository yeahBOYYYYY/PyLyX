from os.path import expanduser, exists, split, splitext, join, abspath
from string import ascii_letters
from json import load


def find_version():
    for i in range(9, -1, -1):
        path = f'{DRIVE}:\\Program Files\\LyX 2.{i}'
        if exists(path):
            version = 2 + 0.1 * i
            user_dir = f'{USER}\\AppData\\Roaming\\LyX{version}'
            return version, path, user_dir
    raise FileNotFoundError(f'Make sure LyX is installed on your computer,\nI can not found it in {DRIVE + ":\\Program Files\\LyX 2.x"}')

USER = expanduser('~')
DOWNLOADS_DIR = f'{USER}\\Downloads'
DRIVE = USER[0]
VERSION, LYX_PATH, USER_DIR = find_version()
LYX_EXE, SYS_DIR = join(LYX_PATH, 'bin\\LyX.exe'), join(LYX_PATH, 'Resources')

PREAMBLE, STANDARD, PLAIN_LAYOUT, TEXT, FORMULA, TABLE = 'preamble', 'Standard', 'Plain Layout', 'Text', 'Formula', 'Tabular'
STATUS, USD, DEFAULT = 'status', '$', 'default'
TABLE_TAG, FEATURES, COLUMN = 'lyxtabular', 'features', 'column'
LEFT, RIGHT, CENTER, TOP, MIDDLE, BOTTOM = 'left', 'right', 'center', 'top', 'middle', 'bottom'
TRUE, FALSE, NONE, RANK, SECTION = 'true', 'false', 'none', 'rank', 'section'
HTML, TAG, ATTRIB, CLASS, DIV, META = 'html', 'tag', 'attrib', 'class', 'div', 'meta'
HE, EN = 'he', 'en'

BEGIN, END = '\\begin_', '\\end_'
DOCUMENT, HEADER, BODY, LAYOUT, INSET, DEEPER = 'document', 'header', 'body', 'layout', 'inset', 'deeper'

CURRENT_FILE_PATH = split(abspath(__file__))[0]
LYXFORMAT = 'lyxformat'
CUR_FORMAT = 620
OBJECTS = {}
with open(join(CURRENT_FILE_PATH, 'data\\designs.json'), 'r', encoding='utf8') as f:
    DESIGNS = load(f)
    OBJECTS.update(DESIGNS)
with open(join(CURRENT_FILE_PATH, 'data\\layouts.json'), 'r', encoding='utf8') as f:
    LAYOUTS = load(f)
    OBJECTS.update(LAYOUTS)
with open(join(CURRENT_FILE_PATH, 'data\\insets.json'), 'r', encoding='utf8') as f:
    INSETS = load(f)
    OBJECTS.update(INSETS)
with open(join(CURRENT_FILE_PATH, 'data\\primary_objects.json'), 'r', encoding='utf8') as f:
    PRIMARIES = load(f)
    OBJECTS.update(PRIMARIES)


def cell2lyx(cell_obj, alignment=LEFT, valignment=TOP,
                topline=TRUE, bottomline=FALSE, leftline=TRUE, rightline=FALSE, usebox=NONE):
    head = f'<cell alignment="{alignment}" valignment="{valignment}" topline="{topline}" bottomline="{bottomline}" "' \
           f'leftline="{leftline}" rightline="{rightline}" usebox="{usebox}">'
    content = ''
    for child in cell_obj:
        content += child.obj2lyx()
    foot = '</cell>\n'
    return head + content + foot


def table2lyx(table: list[list[str]], tabularvalignment=MIDDLE, column_alignment=LEFT, valignment=TOP):
    if is_table(table):
        length = len(table)
        width = len(table[0])
    else:
        raise TypeError(f'invalid table: {table}')

    head = f'\n<lyxtabular version="3" rows="{length}" columns="{width}">\n' \
            f'<features tabularvalignment="{tabularvalignment}" />\n' \
            + width * f'<column alignment="{column_alignment}" valignment="{valignment}" />\n'

    content = ''
    for row in range(length):
        content += '<row>\n'
        for col in range(width):
            r = TRUE if col == width - 1 else FALSE
            b = TRUE if row == length - 1 else FALSE
            content += cell2lyx(table[row][col], bottomline=b, rightline=r)
        content += '</row>\n'

    foot = '</lyxtabular>\n'

    return head + content + foot


def is_table(table):
    if (type(table) is not list) or (not table):
        return False
    length = len(table)
    width = len(table[0])
    for row in range(length):
        if len(table[row]) != width:
            return False
        for col in range(width):
            if type(table[row][col]) is not str:
                return False
    return True


def detect_lang(text: str):
    for char in text:
        if char in 'אבגדהוזחטיכלמנסעפצקרשת':
            return HE
        elif char in ascii_letters:
            return EN
    return ''


def correct_name(full_path: str, extension: str):
    extension = extension if extension.startswith('.') else '.' + extension
    path, name = split(full_path)
    name = splitext(name)[0]
    path = join(path, name + extension)
    return path
