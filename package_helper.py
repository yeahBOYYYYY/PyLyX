from os.path import split, splitext, join
from string import ascii_letters


def correct_name(full_path: str, extension: str) -> str:
    extension = extension if extension.startswith('.') else '.' + extension
    path, name = split(full_path)
    name = splitext(name)[0]
    path = join(path, name + extension)
    return path


def detect_lang(text: str):
    for char in text:
        if char in 'אבגדהוזחטיכלמנסעפצקרשת':
            return 'he'
        elif char in ascii_letters:
            return 'en'
    return ''


def default_path(old_path, new_extension, new_path=None):
    if new_path is not None:
        return correct_name(new_path, new_extension)
    else:
        return correct_name(old_path, new_extension)
