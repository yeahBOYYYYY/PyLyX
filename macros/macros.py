from PyLyX.helper import *
from sys import argv
from os.path import join
from json import dumps


def translate_macros(macros_file: str):
    dictionary = {}
    with open(macros_file, 'r', encoding='utf8') as f:
        for line in f:
            if line == BEGIN_INSET + ' FormulaMacro':
                lst = f.readline().split('{')
                key, value = lst[1][:-1], lst[2][:-1]
                dictionary[key]= value
    return dictionary


def main():
    if len(argv) > 1:
        input_path = argv[1]
        output_path = argv[2] if len(argv) > 2 else join(DOWNLOADS_DIR, 'macros.json')
    else:
        raise Exception('input is empty')

    d = translate_macros(input_path)
    s = dumps(d)
    with open(output_path, 'w', encoding='utf8') as f:
        f.write(s)
