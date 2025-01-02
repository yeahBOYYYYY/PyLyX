from xml.etree.ElementTree import ElementTree
from subprocess import run, CalledProcessError, TimeoutExpired
from PyLyX.data.data import LYX_EXE, VERSION, CUR_FORMAT, BACKUP_DIR
from PyLyX.objects.loader import load
from PyLyX.lyx2xhtml.converter import convert
from PyLyX.package_helper import correct_name, default_path
from PyLyX.init_helper import *


class LyX:
    def __init__(self, full_path: str, writeable=True, doc_obj: Environment | None = None):
        if type(full_path) is not str:
            raise TypeError(f'full_path must be string, not {type(full_path)}.')
        self.__full_path = correct_name(full_path, '.lyx')
        self.__writeable = bool(writeable)

        if doc_obj is not None:
            if type(doc_obj) is not Environment:
                raise TypeError(f'invalid document object: type of {doc_obj} is not {Environment.NAME}.')
            elif not doc_obj.is_command('document'):
                raise TypeError(f'invalid document object: command of {doc_obj} is not "document", but {doc_obj.command()}.')
            elif exists(self.__full_path):
                self.__doc = merge_docs(load(self.__full_path), doc_obj)
            else:
                self.__doc = doc_obj
        elif exists(self.__full_path):
            self.__doc = load(self.__full_path)
            if not self.__writeable:
                self.__doc.set('original_file', self.__full_path)
        else:
            self.__doc = Environment('document')
            self.__doc.extend((Environment('header'), Environment('body')))

    def save_as(self, path: str):
        if type(path) is not str:
            raise TypeError(f'path must be string, not {type(path)}.')
        elif exists(path):
            raise FileExistsError(f'path {path} is exists!')
        else:
            path = correct_name(path, '.lyx')
            with open(path, 'x', encoding='utf8') as file:
                file.write(f'#LyX {VERSION} created this file. For more info see https://www.lyx.org/\n\\lyxformat {CUR_FORMAT}\n')
                file.write(self.__doc.obj2lyx())

    def save(self, backup=True):
        if not self.__writeable:
            raise Exception(f'{self} is not writeable.')
        else:
            self.backup(backup)
            path = self.__full_path + '_'
            if exists(path):
                remove(path)
            with open(path, 'x', encoding='utf8') as file:
                file.write(f'#LyX {VERSION} created this file. For more info see https://www.lyx.org/\n\\lyxformat {CUR_FORMAT}\n')
                file.write(self.__doc.obj2lyx())
            if exists(self.__full_path):
                remove(self.__full_path)
            rename(self.__full_path + '_', self.__full_path)

    def backup(self, active=True):
        if active and exists(self.__full_path):
            name = split(self.__full_path)[1]
            copy(self.__full_path, join(BACKUP_DIR, name))

    def get_path(self) -> str:
        return self.__full_path

    def get_doc(self) -> Environment:
        return self.__doc

    def is_writeable(self):
        return self.__writeable

    def append(self, obj: LyXobj | Environment | Container):
        result = rec_append(self.__doc[1], obj)
        if not result:
            print(f'an error occurred when try append {obj} to {self.__doc[1]}')

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
            raise FileNotFoundError(f'Make sure the path "{LYX_EXE}" is lyx.exe path.')
        return False

    def export2xhtml(self, output_path=None, css_files=(), js_files=(), keep=None, style=None):
        output_path = default_path(self.__full_path, '.xhtml', output_path)
        root, info = convert(self.__doc, css_files, js_files)
        xhtml_keep(output_path, keep)
        xhtml_style(root, output_path, style, info)
        xhtml_write(root, output_path)
        return True

    def export2xml(self, output_path=''):
        if not output_path:
            output_path = self.__full_path.replace('.lyx', '.xml')
        else:
            output_path = correct_name(output_path, '.xml')
        xml = ElementTree(self.__doc)
        xml.write(output_path)

    def find(self, query, command=None, category=None, details=None):
        return rec_find(self.__doc[1], query, command, category, details)

    def find_and_replace(self, old_str, new_str, command=None, category=None, details=None, backup=True):
        self.backup(backup)
        rec_find_and_replace(self.__doc, old_str, new_str, command, category, details)
        self.save()

    def reverse_rtl_links(self, backup=True) -> bool:
        self.backup(backup)
        return line_functions(self, one_link)

    def update_version(self, backup=True) -> bool:
        with open(self.__full_path, 'r', encoding='utf8') as file:
            first_line = file.readline()
            if first_line.startswith(f'#LyX {VERSION}'):
                already_updated = True
            else:
                self.export('lyx')
                already_updated = False

        if VERSION == 2.4 and not already_updated:
            self.reverse_rtl_links(backup)

        return not already_updated
