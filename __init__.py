from xml.etree.ElementTree import ElementTree
from subprocess import run, CalledProcessError, TimeoutExpired
from data.data import LYX_EXE, VERSION, CUR_FORMAT, BACKUP_DIR
from objects.loader import load
from lyx2xhtml.converter import convert
from package_helper import correct_name, default_path
from init_helper import *


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

    def export(self, fmt: str, output_path='', timeout=60) -> bool:
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

    def export2xhtml(self, output_path=None, css_files=(), js_files=(), keep=None, style=None):
        default_path(self.__full_path, '.lyx', '.xhtml', output_path)
        root = self.load()
        root, info = convert(root, css_files, js_files)
        xhtml_keep(output_path, keep)
        xhtml_style(root, output_path, style, info)
        xhtml_write(root, output_path)
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

    def find(self, query, command=None, category=None, details=None):
        return rec_find(self.load()[1], query, command, category, details)

    def find_and_replace(self, old_str, new_str, command=None, category=None, details=None):
        doc = self.load()
        rec_find_and_replace(doc, old_str, new_str, command, category, details)
        LyX(self.__full_path + '~', doc_obj=doc)
        remove(self.__full_path)
        rename(self.__full_path + '~', self.__full_path)
