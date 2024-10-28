from os import rename, remove
from os.path import exists, split, splitext, join
from re import sub
from xml.etree.ElementTree import indent, tostring
from shutil import copy
from subprocess import run, CalledProcessError, TimeoutExpired
from string import ascii_letters
from PyLyX.data.data import LYX_EXE, VERSION, CUR_FORMAT
from PyLyX.objects.LyXobj import LyXobj
from PyLyX.objects.Environment import Environment, Container
from PyLyX.objects.loader import load
from PyLyX.lyx2xhtml.converter import convert
from PyLyX.lyx2xhtml.helper import BASIC_CSS, CSS_FOLDER, NUM_TOC, JS_FOLDER


def correct_name(full_path: str, extension: str):
    extension = extension if extension.startswith('.') else '.' + extension
    path, name = split(full_path)
    name = splitext(name)[0]
    path = join(path, name + extension)
    return path


def create_empty_file(full_path: str):
    with open(full_path, 'x', encoding='utf8') as file:
        file.write(f'#LyX {VERSION} created this file. For more info see https://www.lyx.org/\n\\lyxformat {CUR_FORMAT}\n')
        doc, head, body = Environment('document'), Environment('header'), Environment('body')
        doc.append(head)
        doc.append(body)
        file.write(doc.obj2lyx())


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


class LyX:
    def __init__(self, full_path: str, template=None, doc_obj=None):
        self.__full_path = correct_name(full_path, '.lyx')

        if exists(self.__full_path + '_'):
            remove(self.__full_path + '_')

        if not exists(self.__full_path):
            if type(template) is str and exists(template):
                copy(template, self.__full_path)
            elif template is not None:
                print(f'invalid path for template: {template}.')

            if type(doc_obj) is Environment and doc_obj.is_command('document'):
                    if type(template) is not str or not exists(template):
                        with open(self.__full_path, 'x', encoding='utf8') as file:
                            file.write(f'#LyX {VERSION} created this file. For more info see https://www.lyx.org/\n')
                            file.write(f'\\lyxformat {doc_obj.get('lyxformat')}\n')
                    write_obj(self.__full_path, doc_obj)
            elif doc_obj is not None:
                if type(doc_obj) is not Environment:
                    print(f'invalid document object: type of {doc_obj} is not {Environment.NAME}.')
                elif not doc_obj.is_command('document'):
                    print(f'invalid document object: command of {doc_obj} is not "document", but {doc_obj.command()}.')

            if not exists(self.__full_path):
                print('create empty file.')
                create_empty_file(self.__full_path)

    def load(self) -> Environment:
        doc = load(self.__full_path)
        doc.set('original_file', self.__full_path)
        return doc

    def get_path(self) -> str:
        return self.__full_path

    def line_functions(self, func, args=()) -> bool:
        if exists(self.__full_path + '_'):
            remove(self.__full_path + '_')

        is_changed = False
        with open(self.__full_path, 'r', encoding='utf8') as old:
            with open(self.__full_path + '_', 'x', encoding='utf8') as new:
                for line in old:
                    new_line = func(line, *args)
                    if new_line != line:
                        is_changed = True
                    new.write(new_line)

        if is_changed:
            remove(self.__full_path)
            rename(self.__full_path + '_', self.__full_path)
        else:
            remove(self.__full_path + '_')
        return is_changed

    def write(self, obj):
        write_obj(self.__full_path, obj)

    def find(self, query: str) -> bool:
        with open(self.__full_path, 'r', encoding='utf8') as file:
            for line in file:
                if query in line:
                    return True

        return False

    def find_and_replace(self, str1, str2) -> bool:
        def func(line):
            return line.replace(str1, str2)

        return self.line_functions(func)

    def export(self, fmt: str, output_path='', timeout=30) -> bool:
        if output_path:
            cmd = [LYX_EXE, '--export-to', fmt, output_path, self.__full_path]
        else:
            cmd = [LYX_EXE, '--export', fmt, self.__full_path]

        try:
            run(cmd, timeout=timeout)
            return True
        except TimeoutExpired:
            print(f'Attempting to export file "{split(self.__full_path)[1]}" took too long.')
        except CalledProcessError as e:
            print(f'An error occurred while converting the file {self.__full_path}, error massage: "{e}"')
            return False
        except FileNotFoundError:
            raise FileNotFoundError(f'Make sure the path "{LYX_EXE}" is correct.')
        return False

    def export2xhtml(self, css_files=(BASIC_CSS, ), css_folder=CSS_FOLDER, js_files=(NUM_TOC, ), js_folder=JS_FOLDER, output_path=''):
        if not output_path:
            output_path = self.__full_path.replace('.lyx', '.xhtml')
        else:
            output_path = correct_name(output_path, '.xhtml')

        root = self.load()
        root = convert(root, css_files, css_folder, js_files, js_folder)
        if exists(output_path):
            answer = input(f'File {output_path} is exist.\nDo you want delete it? (Y/N) ')
            if answer == 'Y':
                remove(output_path)
            else:
                return False
        with open(output_path, 'wb') as f:
            indent(root)
            string = tostring(root, encoding='utf8').decode('utf8')
            for tag in {'span', 'b'}:
                string = sub(f'</{tag}>\\s\\s+', f'</{tag}>', string)
                string = sub(f'\\s\\s+<{tag} ', f'<{tag} ', string)
                string = sub(f'\\s\\s+<{tag}>', f'<{tag}>', string)
            string = string.encode('utf8')
            f.write(string)
        return True

    def reverse_hebrew_links(self) -> bool:
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

        return self.line_functions(one_link)

    def update_version(self) -> bool:
        already_updated = True
        with open(self.__full_path, 'r', encoding='utf8') as file:
            first_line = file.readline()
            if not first_line.startswith(f'#LyX {VERSION}'):
                self.export('lyx')
                already_updated = False

        if VERSION == 2.4 and not already_updated:
            self.reverse_hebrew_links()

        return not already_updated


def detect_lang(text: str):
    for char in text:
        if char in 'אבגדהוזחטיכלמנסעפצקרשת':
            return 'he'
        elif char in ascii_letters:
            return 'en'
    return ''
