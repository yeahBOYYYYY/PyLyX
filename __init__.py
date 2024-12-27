from os import rename, remove
from os.path import exists, split, join
from re import sub
from xml.etree.ElementTree import indent, tostring, ElementTree
from shutil import copy
from subprocess import run, CalledProcessError, TimeoutExpired
from data.data import LYX_EXE, VERSION, CUR_FORMAT, BACKUP_DIR
from objects.LyXobj import LyXobj
from objects.Environment import Environment, Container
from objects.loader import load
from lyx2xhtml.converter import convert
from helper import correct_name, detect_lang


class LyX:
    def __init__(self, full_path: str, template=None, doc_obj=None, backup=True):
        self.__full_path = correct_name(full_path, '.lyx')

        if backup and exists(self.__full_path):
            name = split(self.__full_path)[1]
            copy(self.__full_path, join(BACKUP_DIR, name))

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
                with open(self.__full_path, 'x', encoding='utf8') as file:
                    file.write(f'#LyX {VERSION} created this file. For more info see https://www.lyx.org/\n\\lyxformat {CUR_FORMAT}\n')
                    doc, head, body = Environment('document'), Environment('header'), Environment('body')
                    doc.append(head)
                    doc.append(body)
                    file.write(doc.obj2lyx())

    def get_path(self) -> str:
        return self.__full_path

    def load(self) -> Environment:
        doc = load(self.__full_path)
        doc.set('original_file', self.__full_path)
        return doc

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

    def export2xhtml(self, output_path='', keep=None, css_files=(), js_files=()):
        if not output_path:
            output_path = self.__full_path.replace('.lyx', '.xhtml')
        else:
            output_path = correct_name(output_path, '.xhtml')

        root = self.load()
        root = convert(root, css_files, js_files)
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

    def export2xml(self, output_path=''):
        if not output_path:
            output_path = self.__full_path.replace('.lyx', '.xml')
        else:
            output_path = correct_name(output_path, '.xml')
        xml = ElementTree(self.load())
        xml.write(output_path)

    def write(self, obj):
        write_obj(self.__full_path, obj)

    def reverse_rtl_links(self) -> bool:
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

        return line_functions(self, one_link)

    def update_version(self) -> bool:
        already_updated = True
        with open(self.__full_path, 'r', encoding='utf8') as file:
            first_line = file.readline()
            if not first_line.startswith(f'#LyX {VERSION}'):
                self.export('lyx')
                already_updated = False

        if VERSION == 2.4 and not already_updated:
            self.reverse_rtl_links()

        return not already_updated


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
        rename(path + '_', lyx_file.__full_path)
    else:
        remove(path + '_')
    return is_changed


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
