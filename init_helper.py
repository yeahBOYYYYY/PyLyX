from os import rename, remove
from os.path import exists, join, split
from re import sub
from xml.etree.ElementTree import indent, tostring, Element
from shutil import copy
from PyLyX.data.data import USER_DIR
from PyLyX.objects.LyXobj import LyXobj
from PyLyX.objects.Environment import Environment, Container
from PyLyX.package_helper import detect_lang


def rec_append(obj1: LyXobj | Environment | Container, obj2: LyXobj | Environment | Container):
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
    start = 'name "'
    end = '"\n'
    if line.startswith(start) and line.endswith(end):
        text = line[len(start):-len(end)]
        if detect_lang(text) == 'he':
            lst = text.split()
            lst.reverse()
            text = ' '.join(lst)
            line = start + text + end
    return line


def xhtml_remove(output_path: str, remove_old: bool | None = None):
    if exists(output_path):
        if remove_old is None:
            answer = ''
            while answer not in {'Y', 'N'}:
                answer = input(f'File {output_path} is exist.\nDo you want delete it? (Y/N) ')
            remove_old = True if answer == 'Y' else False
        if remove_old:
            remove(output_path)


def xhtml_style(root: Environment | Element, output_path: str, css_copy: bool | None = None, info: dict | None = None):
    if (css_copy is None and info.get('html_css_as_file') == 1) or css_copy is True:
        for e in root[0].iterfind("link[@type='text/css']"):
            full_path = e.get('href')
            path = split(output_path)[0]
            name = split(full_path)[1]
            copy(full_path, join(path, name))
            e.set('href', name)
    elif css_copy is None and info is not None and info.get('html_css_as_file') == 0:
        css_copy = LyXobj('style')
        for e in root[0].iterfind("link[@type='text/css']"):
            with open(e.get('href'), 'r') as f:
                css_copy.text = css_copy.text + f.read()
            root[0].remove(e)
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

    indent(root)
    xhtml_string = tostring(root, encoding='utf8').decode('utf8')
    for tag in {'span', 'b', 'u', 'i'}:
        xhtml_string = sub(f'</{tag}>\\s\\s+', f'</{tag}>', xhtml_string)
        xhtml_string = sub(f'\\s\\s+<{tag} ', f'<{tag} ', xhtml_string)
        xhtml_string = sub(f'\\s\\s+<{tag}>', f'<{tag}>', xhtml_string)
    return xhtml_string


def rec_find(obj, query, command=None, category=None, details=None) -> bool:
    if command is not None and obj.obj_props() != f'{command} {category} {details}':
        return False
    elif query in obj.text or query in obj.tail:
        return True
    for e in obj:
        if rec_find(e, query, command, category, details):
            return True
    return False


def rec_find_and_replace(obj, old_str, new_str, command=None, category=None, details=None):
    if command is None or obj.obj_props() == f'{command} {category} {details}':
        obj.text = obj.text.replace(old_str, new_str)
        obj.tail = obj.tail.replace(old_str, new_str)
        for key in obj.attrib:
            obj.attrib[key] = obj.attrib[key].replace(old_str, new_str)
    for e in obj:
        rec_find_and_replace(e, old_str, new_str, command, category, details)


def export_bug_fix():
    preferences = join(USER_DIR, 'preferences')
    with open(preferences, 'r', encoding='utf8') as old:
        with open(preferences + '_n', 'w', encoding='utf8') as new:
            for line in old:
                if line.startswith(r'\ui_style'):
                    line = '#' + line
                elif line.startswith(r'#\ui_style'):
                    line = line[1:]
                new.write(line)
    remove(preferences)
    rename(preferences + '_n', preferences)
