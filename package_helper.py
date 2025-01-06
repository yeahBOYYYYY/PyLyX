from os.path import split, splitext, join
from string import ascii_letters
from PyLyX.objects.LyXobj import LyXobj

MATHJAX = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js'


def correct_name(full_path: str, extension: str) -> str:
    extension = extension if extension.startswith('.') else '.' + extension
    path, name = split(full_path)
    name = splitext(name)[0]
    path = join(path, name + extension)
    return path


def default_path(old_path, new_extension, new_path=None):
    if new_path is not None:
        return correct_name(new_path, new_extension)
    else:
        return correct_name(old_path, new_extension)


def detect_lang(text: str):
    for char in text:
        if char in 'אבגדהוזחטיכלמנסעפצקרשת':
            return 'he'
        elif char in ascii_letters:
            return 'en'
    return ''


def correct_brackets(text: str, is_open: bool):
    new_text = ''
    for char in text:
        if char in {'(', ')'}:
            if is_open:
                new_text += ')'
            else:
                new_text += '('
            is_open = not is_open
        else:
            new_text += char
    return new_text, is_open


def run_correct_brackets(obj: LyXobj):
    is_open = False
    for e in obj.iter():
        if not e.is_category({'Formula', 'FormulaMacro'}):
            e.text , is_open = correct_brackets(e.text, is_open)
        e.tail, is_open = correct_brackets(e.tail, is_open)


def create_css(path: str):
    path = correct_name(path, '.css')
    attrib = {'rel': 'stylesheet', 'type': 'text/css', 'href': path}
    return LyXobj('link', attrib=attrib)


def create_script(source: str, async_=''):
    attrib = {'src': source}
    if async_:
        attrib['async'] = async_
    return LyXobj('script', attrib=attrib)


def mathjax():
    return create_script(MATHJAX, 'async')


def viewport():
    attrib = {'name': 'viewport', 'content': 'width=device-width'}
    return LyXobj('meta', attrib=attrib)
