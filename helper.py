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

CURRENT_FILE_PATH = split(abspath(__file__))[0]

with open(join(CURRENT_FILE_PATH, 'data\\key_words.json'), 'r', encoding='utf8') as f:
    KEY_WORDS = load(f)

with open(join(CURRENT_FILE_PATH, 'data\\layouts.json'), 'r', encoding='utf8') as f:
    LAYOUTS = load(f)
with open(join(CURRENT_FILE_PATH, 'data\\insets.json'), 'r', encoding='utf8') as f:
    INSETS = load(f)
with open(join(CURRENT_FILE_PATH, 'data\\commands.json'), 'r', encoding='utf8') as f:
    ENVIRONMENTS = load(f)
    ENVIRONMENTS.update(LAYOUTS)
    ENVIRONMENTS.update(INSETS)

USER = expanduser('~')
DRIVE = USER[0]
VERSION, LYX_PATH, USER_DIR = find_version()
LYX_EXE, SYS_DIR = join(LYX_PATH, 'bin\\LyX.exe'), join(LYX_PATH, 'Resources')
FORMAT = 620
DOWNLOADS_DIR = f'{USER}\\Downloads'

TEXT, FORMULA, STANDARD, PLAIN_LAYOUT, TABLE, USD = 'Text', 'Formula', 'Standard', 'Plain Layout', 'Tabular', '$'
LEFT, RIGHT, CENTER, TOP, MIDDLE, BOTTOM = 'left', 'right', 'center', 'top', 'middle', 'bottom'
TRUE, FALSE, NONE, RANK, SECTION = 'true', 'false', 'none', 'rank', 'section'
TAG, ATTRIB = 'tag', 'attrib'
HE, EN = 'he', 'en'
# LANGUAGES = {RIGHT: {HE}, LEFT: {EN}}

BEGIN, END = '\\begin_', '\\end_'
DOCUMENT, HEADER, BODY, LAYOUT, INSET, DEEPER = 'document', 'header', 'body', 'layout', 'inset', 'deeper'


def create_layout(layout: str, content: str, align=''):
    head = f'\n{BEGIN}{LAYOUT} {layout}\n'
    if align:
        head += f'\\align {align}\n'
    foot = f'\n{END}{LAYOUT}\n'
    return head + content + foot


def create_inset(inset: str, content: str):
    head = f'\n{BEGIN}{INSET} {inset}\n'
    foot = f'\n{END}{INSET}\n'
    return head + content + foot


def create_cell(content: str, alignment=LEFT, valignment=TOP,
                topline=TRUE, bottomline=FALSE, leftline=TRUE, rightline=FALSE, usebox=NONE):
    head = f'<cell alignment="{alignment}" valignment="{valignment}" topline="{topline}" bottomline="{bottomline}" "' \
           f'leftline="{leftline}" rightline="{rightline}" usebox="{usebox}">'
    content = create_layout(PLAIN_LAYOUT, content)
    content = create_inset(TEXT, content)
    foot = '</cell>\n'
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


def create_table(table: list[list], tabularvalignment=MIDDLE, column_alignment=LEFT, valignment=TOP):
    if is_table(table):
        length = len(table)
        width = len(table[0])
    else:
        raise TypeError(f'invalid table: {table}')

    head = f'\n<lyxtabular version="3" rows="{length}" columns="{width}">\n' \
            f'<features tabularvalignment="{tabularvalignment}">\n' \
            + width * f'<column alignment="{column_alignment}" valignment="{valignment}">\n'

    content = ''
    for row in range(length):
        content += '<row>\n'
        for col in range(width):
            r = TRUE if col == width - 1 else FALSE
            b = TRUE if row == length - 1 else FALSE
            content += create_cell(table[row][col], bottomline=b, rightline=r)
        content += '</row>\n'

    foot = '</lyxtabular>\n'

    return head + content + foot


def detect_lang(text: str):
    for char in text:
        if char in 'אבגדהוזחטיכלמנסעפצקרשת':
            return HE
        elif char in ascii_letters:
            return EN
    return ''


def correct_name(name: str, extension: str):
    path, name = split(name)
    name = splitext(name)[0]
    path = join(path, name + extension)
    return path
