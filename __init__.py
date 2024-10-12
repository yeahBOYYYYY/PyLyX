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
PACKAGE_PATH = split(abspath(__file__))[0]

CUR_FORMAT = 620

OBJECTS = {}
with open(join(PACKAGE_PATH, 'data\\designs.json'), 'r', encoding='utf8') as f:
    DESIGNS = load(f)
    OBJECTS.update(DESIGNS)
with open(join(PACKAGE_PATH, 'data\\par_set.json'), 'r', encoding='utf8') as f:
    PAR_SET = load(f)
    OBJECTS.update(PAR_SET)
with open(join(PACKAGE_PATH, 'data\\layouts.json'), 'r', encoding='utf8') as f:
    LAYOUTS = load(f)
    OBJECTS.update(LAYOUTS)
with open(join(PACKAGE_PATH, 'data\\insets.json'), 'r', encoding='utf8') as f:
    INSETS = load(f)
    OBJECTS.update(INSETS)
with open(join(PACKAGE_PATH, 'data\\primary_objects.json'), 'r', encoding='utf8') as f:
    PRIMARIES = load(f)
    OBJECTS.update(PRIMARIES)
with open(join(PACKAGE_PATH, 'data\\ends.json'), 'r', encoding='utf8') as f:
    ENDS = load(f)


def detect_lang(text: str):
    for char in text:
        if char in 'אבגדהוזחטיכלמנסעפצקרשת':
            return 'he'
        elif char in ascii_letters:
            return 'en'
    return ''


def correct_name(full_path: str, extension: str):
    extension = extension if extension.startswith('.') else '.' + extension
    path, name = split(full_path)
    name = splitext(name)[0]
    path = join(path, name + extension)
    return path


def xml2txt(text: str):
    dictionary = {'quot;': '"', 'amp;': '&', 'apos;': "'", 'lt;': '<', 'gt;': '>'}
    for key in dictionary:
        text = text.replace('&' + key, dictionary[key])
        text = text.replace(key, dictionary[key])
    return text


def is_known_object(command: str, category: str, details: str):
    return command in OBJECTS and category in OBJECTS[command] and details in OBJECTS[command][category]
