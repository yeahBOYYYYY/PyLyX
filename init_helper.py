"""
Helper functions for LyX file initialization and manipulation.

This module provides utility functions for:
- Recursively appending objects to document structures
- Processing LyX files line by line
- Handling file removal and XHTML styling
- Finding and replacing content in document trees
- Managing LyX export bugs and preferences
"""

from os import rename, remove
from os.path import exists, join, split
from xml.etree.ElementTree import Element
from shutil import copy
from PyLyX.data.data import VERSION, CUR_FORMAT, USER_DIR, RTL_LANGS
from PyLyX.objects.LyXobj import LyXobj
from PyLyX.objects.Environment import Environment, Container
from PyLyX.package_helper import detect_lang

# the first and the second lines in any LyX document.
PREFIX = f'#LyX {VERSION} created this file. For more info see https://www.lyx.org/\n\\lyxformat {CUR_FORMAT}\n'


def rec_append(obj1: LyXobj | Environment | Container | Element, obj2: LyXobj | Environment | Container):
    """
    Recursively append an object to a document structure.
    
    Finds the appropriate location in the document tree to append obj2,
    respecting nesting rules and object ranks. Tries to append to the
    deepest valid location first.
    
    :param obj1: The parent object to append to
    :param obj2: The object to append
    :return: True if appending was successful, False otherwise
    """
    obj1.open()
    if len(obj1) == 0:
        if obj2.can_be_nested_in(obj1)[0]:
            obj1.append(obj2)
            return True
    else:
        for i in range(len(obj1)-1, -1, -1):
            if rec_append(obj1[i], obj2):
                return True
        if obj2.can_be_nested_in(obj1)[0]:
            obj1.append(obj2)
            return True
    return False


def line_functions(lyx_file, func, args=()) -> bool:
    """
    Apply a function to each line of a LyX file.
    
    Processes the file line by line, applying the given function to each line.
    If any lines are modified, the file is updated; otherwise, it remains unchanged.
    Uses a temporary file for safe processing.
    
    :param lyx_file: LyX file object to process
    :param func: Function to apply to each line (takes line as first argument)
    :param args: Additional arguments to pass to the function
    :return: True if the file was modified, False otherwise
    """
    path = lyx_file.get_path()

    is_changed = False
    with open(path, 'r', encoding='utf8') as old:
        with open(path + '_', 'x', encoding='utf8') as new:
            for line in old:
                new_line = func(line, *args)
                if new_line != line:
                    is_changed = True
                new.write(new_line)

    if is_changed:
        remove(path)
        rename(path + '_', lyx_file.get_path())
    else:
        remove(path + '_')
    return is_changed


def one_link(line: str):
    """
    Process a link name line for RTL (right-to-left) languages.
    
    If the line contains a name attribute and the text is in an RTL language,
    reverses the word order to display correctly in RTL contexts.
    
    :param line: A line containing a name attribute
    :return: The processed line (reversed if RTL, unchanged otherwise)
    """
    start = 'name "'
    end = '"\n'
    if line.startswith(start) and line.endswith(end):
        text = line[len(start):-len(end)]
        if detect_lang(text) in RTL_LANGS:
            lst = text.split()
            lst.reverse()
            text = ' '.join(lst)
            line = start + text + end
    return line


def old_file_remove(output_path: str, remove_old: bool | None = None):
    """
    Handle removal of existing output file.
    
    If the output file exists and remove_old is None, prompts the user
    for confirmation. If remove_old is True, removes the file without prompting.
    
    :param output_path: Path to the output file
    :param remove_old: Whether to remove the old file (None prompts user, True removes, False keeps)
    """
    if exists(output_path):
        if remove_old is None:
            answer = ''
            while answer not in {'Y', 'N'}:
                answer = input(f'File {output_path} is exist.\nDo you want delete it? (Y/N) ')
            remove_old = True if answer == 'Y' else False
        if remove_old:
            remove(output_path)


def xhtml_style(root: Environment | Element, output_path: str, css_copy: bool | None = None, info: dict | None = None):
    """
    Apply styling and finalize XHTML output.
    
    Handles CSS file linking or embedding, copies image files to output directory,
    and fixes whitespace issues in inline elements.
    
    :param root: Root element of the XHTML document
    :param output_path: Path where the XHTML file will be saved
    :param css_copy: Whether to copy CSS files (True), embed them (False), or use document setting (None)
    :param info: Document information dictionary containing styling preferences
    """
    if (css_copy is None and info.get('html_css_as_file') == 1) or css_copy is True:
        for e in root[0].iterfind("link[@type='text/css']"):
            full_path = e.get('href')
            path = split(output_path)[0]
            name = split(full_path)[1]
            if exists(full_path):
                copy(full_path, join(path, name))
            else:
                print(f'invalid path: {full_path}')
            e.set('href', name)
    elif css_copy is None and info is not None and info.get('html_css_as_file') == 0:
        css_copy = LyXobj('style')
        for e in root[0].iterfind("link[@type='text/css']"):
            full_path = e.get('href', '')
            if exists(full_path):
                with open(full_path, 'r') as f:
                    css_copy.text = css_copy.text + f.read()
                root[0].remove(e)
            else:
                print(f'invalid path: {full_path}')
        root[0].append(css_copy)

    for e in root[0].iterfind("img"):
        img_path = e.get('src', '')
        if exists(img_path):
            img_name = img_path.split('\\')[-1]
            path = split(output_path)[0]
            copy(img_path, join(path, img_name))
            e.set('src', img_name)
        else:
            print(f'image path is not found: {img_path}')

    last = root
    whitespaces = {' ', '\t', '\n'}
    for cur in root.iter():
        if cur.tag in {'span', 'b', 'u', 'i'}:
            if len(cur.tail) > 1 and cur.tail[0] in whitespaces and cur.tail[1] in whitespaces:
                cur.text = cur.text.lstrip()
            if len(last.tail) > 1 and last.tail[-1] in whitespaces and last.tail[-2] in whitespaces:
                last.text = last.text.rstrip()
        last = cur


def rec_find(obj: LyXobj | Environment | Container | Element, query: str | None, command='', category='', details='')\
        -> LyXobj | Environment | Container | Element | None:
    """
    Recursively find an element in the document tree.
    
    Searches for an element that either:
    - Contains the query string in its text or tail
    - Matches the specified command/category/details properties
    
    :param obj: Root object to search from
    :param query: Text to search for (or None to search by properties only)
    :param command: Filter by command attribute
    :param category: Filter by category attribute
    :param details: Filter by details attribute
    :return: First matching element, or None if not found
    :raises TypeError: If neither query nor object properties are specified
    """
    if command:
        if obj.obj_props() == (command, category, details):
            if query is None or query in obj.text or query in obj.tail:
                return obj
            else:
                for e in obj:
                    result = rec_find(e, query, command, category, details)
                    if result is not None:
                        return obj
    elif query is None:
        raise TypeError('please give query or object properties.')
    else:
        if query in obj.text or query in obj.tail:
            return obj
        for e in obj:
            result = rec_find(e, query, command, category, details)
            if result is not None:
                return result


def rec_find_and_replace(obj, old_str, new_str, command='', category='', details=''):
    """
    Recursively find and replace text in the document tree.
    
    Replaces all occurrences of old_str with new_str in:
    - Element text content
    - Element tail content
    - Element attributes
    
    Can be filtered to only replace in elements with specific properties.
    
    :param obj: Root object to search from
    :param old_str: String to find
    :param new_str: String to replace with
    :param command: Only replace in elements with this command (empty string = all)
    :param category: Only replace in elements with this category (empty string = all)
    :param details: Only replace in elements with this details (empty string = all)
    """
    if command and obj.obj_props() != (command, category, details):
        obj.text = obj.text.replace(old_str, new_str)
        obj.tail = obj.tail.replace(old_str, new_str)
        for key in obj.attrib:
            obj.attrib[key] = obj.attrib[key].replace(old_str, new_str)
    for e in obj:
        rec_find_and_replace(e, old_str, new_str, command, category, details)


def export_bug_fix(before: bool):
    """
    Workaround for LyX export bug by temporarily modifying preferences.
    
    Temporarily comments/uncomments the ui_style preference in LyX's
    preferences file to work around export issues.
    
    :param before: True to comment out ui_style (before export), False to restore it (after export)
    """
    preferences = join(USER_DIR, 'preferences')
    with open(preferences, 'r', encoding='utf8') as old:
        with open(preferences + '_n', 'w', encoding='utf8') as new:
            if before:
                for line in old:
                    if line.startswith(r'\ui_style'):
                        line = '#' + line
                    new.write(line)
            else:
                for line in old:
                    if line.startswith(r'#\ui_style'):
                        line = line[1:]
                    new.write(line)
    remove(preferences)
    rename(preferences + '_n', preferences)
