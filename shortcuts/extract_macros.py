"""
Module for extracting LaTeX macros from LyX files.

This module provides utilities to:
- Extract macro definitions from LyX documents
- Convert macros to JSON format
- Translate macro dictionaries between different formats
"""

from sys import argv
from os.path import join
from json import dumps, load
from PyLyX.package_helper import correct_name
from PyLyX.data.data import DOWNLOADS_DIR


def translate_dicts(primary: dict, secondary: dict):
    """
    Translate between two macro dictionaries by finding matching values.
    
    Creates a translation dictionary where keys from the secondary dictionary
    are mapped to keys from the primary dictionary that have the same value.
    
    :param primary: The primary macro dictionary to translate to
    :param secondary: The secondary macro dictionary to translate from
    :return: Dictionary mapping secondary keys to primary keys with matching values
    """
    dictionary = {}
    for key in secondary:
        for k in primary:
            if secondary[key] == primary[k]:
                dictionary[key] = k
    return dictionary


def translate_json(primary: str, secondary: str, output_path=join(DOWNLOADS_DIR, 'macros.json')):
    """
    Translate macro definitions between two JSON files.
    
    Loads two JSON macro dictionaries, creates a translation mapping,
    and saves the result to an output file.
    
    :param primary: Path to the primary JSON macro file
    :param secondary: Path to the secondary JSON macro file
    :param output_path: Path where the translation dictionary will be saved (default: Downloads/macros.json)
    """
    primary, secondary = correct_name(primary, '.json'), correct_name(secondary, '.json')
    with open(primary, 'r', encoding='utf8') as file:
        primary = load(file)
    with open(secondary, 'r', encoding='utf8') as file:
        secondary = load(file)
    dictionary = translate_dicts(primary, secondary)
    string = dumps(dictionary)
    with open(output_path, 'w', encoding='utf8') as file:
        file.write(string)


def one_macro(line: str):
    """
    Parse a single macro definition line from a LyX file.
    
    Extracts the macro name (key) and its LaTeX definition (value) from
    a line containing a LyX FormulaMacro inset.
    
    Expected format: \\newcommand{\\macroname}{latex_definition}
    
    :param line: A line containing a macro definition
    :return: Tuple of (macro_name, macro_definition)
    """
    key = ''
    value = ''

    i = 0
    while line[i] != '{':
        i += 1
    i += 1
    while line[i] != '}':
        key += line[i]
        i += 1
    i += 1
    while line[i] != '{':
        i += 1
    i += 1
    while not (line[i] == '}' and line[i + 1] == '\n'):
        value += line[i]
        i += 1

    return key, value


def extract_macros(macros_file: str):
    """
    Extract all macro definitions from a LyX file.
    
    Scans through a LyX file and finds all FormulaMacro insets,
    extracting the macro definition lines.
    
    :param macros_file: Path to the LyX file containing macros
    :return: List of macro definition lines
    """
    lines = []
    with open(macros_file, 'r', encoding='utf8') as file:
        for line in file:
            if line ==  '\\begin_inset FormulaMacro\n':
                lines.append(file.readline())
    return lines


def main():
    """
    Main entry point for the macro extraction script.
    
    Command line usage:
        python extract_macros.py <input_lyx_file> [output_json_file]
    
    Extracts all macros from the input LyX file and saves them as JSON.
    If no output path is specified, saves to Downloads/macros.json.
    
    :raises Exception: If no input file is provided
    """
    if len(argv) > 1:
        input_path = argv[1]
        output_path = argv[2] if len(argv) > 2 else join(DOWNLOADS_DIR, 'macros.json')
    else:
        raise Exception('input is empty')

    lines = extract_macros(input_path)
    dictionary = dict([one_macro(line) for line in lines])
    string = dumps(dictionary)
    with open(output_path, 'w', encoding='utf8') as file:
        file.write(string)


if __name__ == '__main__':
    main()
