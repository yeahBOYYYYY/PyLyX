from xml.etree.ElementTree import ElementTree, tostring, indent
from subprocess import run, CalledProcessError, TimeoutExpired
from PyLyX.data.data import LYX_EXE, VERSION, CUR_FORMAT, BACKUP_DIR
from PyLyX.objects.loader import load
from PyLyX.xhtml.converter import convert
from PyLyX.package_helper import correct_name, default_path, run_correct_brackets
from PyLyX.init_helper import *

# the first and the second lines in any LyX document.
PREFIX = f'#LyX {VERSION} created this file. For more info see https://www.lyx.org/\n\\lyxformat {CUR_FORMAT}\n'


class LyX:
    """a LyX document."""
    def __init__(self, full_path: str, writeable=True, doc_obj: Environment | None = None):
        if type(full_path) is not str:
            raise TypeError(f'full_path must be a string, not {type(full_path)}.')
        self.__full_path = correct_name(full_path, '.lyx')
        self.__writeable = bool(writeable)

        if exists(self.__full_path):
            if doc_obj is not None:
                raise FileExistsError(f'file {self.__full_path} is exists.')
            self.__doc = load(self.__full_path)
            if not self.__writeable:
                self.__doc.set('original_file', self.__full_path)
        elif type(doc_obj) is Environment:
            if not doc_obj.is_command('document'):
                raise TypeError(f'invalid document object: command of {doc_obj} is not "document", but {doc_obj.command()}.')
            else:
                self.__doc = doc_obj
        else:
            raise TypeError(f'invalid document object: type of {doc_obj} is not {Environment.NAME}.')

    def save_as(self, path: str):
        if type(path) is not str:
            raise TypeError(f'path must be string, not {type(path)}.')
        elif exists(path):
            raise FileExistsError(f'path {path} is exists!')
        else:
            path = correct_name(path, '.lyx')
            with open(path, 'x', encoding='utf8') as file:
                file.write(PREFIX)
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
                file.write(PREFIX)
                if self.__doc.get('lyxformat', CUR_FORMAT) != CUR_FORMAT:
                    run_correct_brackets(self.__doc)
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

    def is_writeable(self) -> bool:
        return self.__writeable

    def append(self, obj: LyXobj | Environment | Container):
        result = rec_append(self.__doc[1], obj)
        if not result:
            print(f'an error occurred when try append {obj} to {self.__doc[1]}')

    def export(self, fmt: str, output_path='', timeout=60) -> bool:
        if output_path:
            output_path = correct_name(output_path, fmt)
            while output_path and output_path[-1] in '1234567890':
                output_path = output_path[:-1]
            cmd = [LYX_EXE, '--export-to', fmt, output_path, self.__full_path]
        else:
            cmd = [LYX_EXE, '--export', fmt, self.__full_path]

        export_bug_fix(True)
        try:
            run(cmd, timeout=timeout, shell=True)
            export_bug_fix(False)
            return True
        except TimeoutExpired:
            print(f'Attempting to export file "{split(self.__full_path)[1]}" took too long time.')
        except CalledProcessError as e:
            print(f'An error occurred while converting the file {self.__full_path}.\nError massage is: "{e}"')
            return False
        except FileNotFoundError:
            print(f'Make sure the path "{LYX_EXE}" is the correct lyx.exe path.')
        export_bug_fix(False)
        return False

    def export2xhtml(self, output_path: str | None = None, css_files=(), js_files=(), remove_old: bool | None = None, css_copy: bool | None = None):
        output_path = default_path(self.__full_path, '.xhtml', output_path)
        old_file_remove(output_path, remove_old)
        root, info = convert(self.__doc, css_files, js_files)
        xhtml_style(root, output_path, css_copy, info)
        indent(root)
        with open(output_path, 'wb') as f:
            f.write(tostring(root, encoding='utf8'))
        return True

    def export2xml(self, output_path=''):
        if not output_path:
            output_path = self.__full_path.replace('.lyx', '.xml')
        else:
            output_path = correct_name(output_path, '.xml')
        xml = ElementTree(self.__doc)
        xml.write(output_path)

    def find(self, query: str | None, command='', category='', details=''):
        return rec_find(self.__doc[1], query, command, category, details)

    def find_and_replace(self, old_str, new_str, command: str | None = None, category: str | None = None, details: str | None = None, backup=True):
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
