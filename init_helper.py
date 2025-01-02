from os import rename, remove
from os.path import exists, join, split
from re import sub
from xml.etree.ElementTree import indent, tostring
from shutil import copy
from PyLyX.objects.LyXobj import LyXobj
from PyLyX.objects.Environment import Environment, Container
from PyLyX.package_helper import detect_lang


def merge_docs(doc1: Environment, doc2: Environment):
    doc = Environment('document')
    doc.append(doc2[0])
    doc.append(doc1[1])
    for e in doc2[1]:
        doc[1].append(e)
    return doc


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


def write_obj(full_path: str, obj):
    if type(obj) not in (Environment, Container):
        raise TypeError(f'obj must be {LyXobj.NAME}, not {type(obj)}.')
    if exists(full_path + '_'):
        remove(full_path)

    if type(obj) is Container or obj.is_command('layout'):
        start = ('\\end_body\n',)
        end = ('\\end_body\n', '\\end_document\n')
    elif obj.is_command('body'):
        start = ('\\begin_body\n',)
        end = ('\\end_document\n',)
    elif obj.is_command('document'):
        start = ('\\begin_document\n',)
        end = ()
    else:
        raise TypeError(f'invalid command of {Environment.NAME} object: {obj.command()}.')

    with open(full_path, 'r', encoding='utf8') as old:
        with open(full_path + '_', 'x', encoding='utf8') as new:
            for line in old:
                if line not in start:
                    new.write(line)
                else:
                    break
            new.write(obj.obj2lyx())
            for s in end:
                new.write(s)

    remove(full_path)
    rename(full_path + '_', full_path)


def xhtml_style(root, output_path: str, style: bool, info: dict):
    if (style is None and info.get('html_css_as_file') == 1) or style is True:
        for e in root[0].iterfind("link[@type='text/css']"):
            full_path = e.get('href')
            path = split(output_path)[0]
            name = split(full_path)[1]
            copy(full_path, join(path, name))
            e.set('href', name)
    elif style is None and info.get('html_css_as_file') == 0:
        style = LyXobj('style')
        for e in root[0].iterfind("link[@type='text/css']"):
            with open(e.get('href'), 'r') as f:
                style.text = style.text + f.read()
            root[0].remove(e)
        root[0].append(style)


def xhtml_write(root, output_path):
    with open(output_path, 'wb') as f:
        indent(root)
        string = tostring(root, encoding='utf8').decode('utf8')
        for tag in {'span', 'b'}:
            string = sub(f'</{tag}>\\s\\s+', f'</{tag}>', string)
            string = sub(f'\\s\\s+<{tag} ', f'<{tag} ', string)
            string = sub(f'\\s\\s+<{tag}>', f'<{tag}>', string)
        string = string.encode('utf8')
        f.write(string)


def xhtml_keep(output_path, keep):
    if exists(output_path):
        if keep is None:
            answer = ''
            while answer not in {'Y', 'N'}:
                answer = input(f'File {output_path} is exist.\nDo you want delete it? (Y/N) ')
            keep = True if answer == 'N' else False
        if not keep:
            remove(output_path)
        else:
            return False


def rec_find(obj, query, command=None, category=None, details=None):
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
    for e in obj:
        rec_find_and_replace(e, old_str, new_str, command, category, details)
