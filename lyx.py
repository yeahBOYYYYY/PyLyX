from os import rename, remove
from shutil import copy
from subprocess import run, CalledProcessError, TimeoutExpired
from PyLyX.helper import *
from PyLyX.environments import Environment
from PyLyX.loader import load


class LyX:
    def __init__(self, full_path: str, template=join(CURRENT_FILE_PATH, 'data\\template.lyx')):
        self.__full_path = correct_name(full_path, '.lyx')

        if exists(self.__full_path + '~'):
            rename(self.__full_path + '~', self.__full_path + '_')
            print(f'the name of file "{self.__full_path + '~'}" is changed to "{self.__full_path + '_'}".')
        if not exists(self.__full_path):
            if type(template) is str and exists(template):
                copy(template, self.__full_path)
            else:
                print(f'invalid path for template: {template},\ncreate empty file instead.')
                with open(self.__full_path, 'x', encoding='utf8') as file:
                    file.write(f'#LyX {VERSION} created this file. For more info see https://www.lyx.org/\n\\lyxformat {FORMAT}\n')
                    doc, head, body = Environment(DOCUMENT), Environment(HEADER), Environment(BODY)
                    doc.append(head)
                    doc.append(body)
                    file.write(str(doc))

    def load_toc(self):
        return load(self.__full_path)

    def line_functions(self, func, args=()) -> bool:
        if exists(self.__full_path + '~'):
            remove(self.__full_path + '~')

        is_changed = False
        with open(self.__full_path, 'r', encoding='utf8') as old:
            with open(self.__full_path + '~', 'x', encoding='utf8') as new:
                for line in old:
                    new_line = func(line, *args)
                    if new_line != line:
                        is_changed = True
                    new.write(new_line)

        if is_changed:
            remove(self.__full_path)
            rename(self.__full_path + '~', self.__full_path)
        else:
            remove(self.__full_path + '~')
        return is_changed


    def write(self, toc: Environment):
        if type(toc) is not Environment:
            raise TypeError(f'toc must be {Environment} object, not {type(toc)}.')
        if exists(self.__full_path + '~'):
            remove(self.__full_path)

        if toc.command() == LAYOUT or toc.is_section():
            start = ()
            end = (f'{END}{BODY}\n', f'{END}{DOCUMENT}\n')
        elif toc.command() == BODY:
            start = (f'{BEGIN}{BODY}\n', )
            end = (f'{END}{DOCUMENT}\n', )
        elif toc.command() == DOCUMENT:
            start = (f'{BEGIN}{DOCUMENT}\n', )
            end = ()
        else:
            raise TypeError(f'invalid command of Environment object: {toc.command()}.')

        with open(self.__full_path, 'r', encoding='utf8') as old:
            with open(self.__full_path + '~', 'x', encoding='utf8') as new:
                for line in old:
                    if line not in (start + end):
                        new.write(line)
                    else:
                        break
                new.write(str(toc))
                for s in end:
                    new.write(s)

        remove(self.__full_path)
        rename(self.__full_path + '~', self.__full_path)

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

    def export(self, fmt: str, output_path='') -> bool:
        if output_path:
            cmd = [LYX_EXE, '--export-to', fmt, output_path, self.__full_path]
        else:
            cmd = [LYX_EXE, '--export', fmt, self.__full_path]

        try:
            run(cmd, timeout=15)
            return True
        except TimeoutExpired:
            print(f'Attempting to export file "{split(self.__full_path)[1]}" took too long.')
        except CalledProcessError as e:
            print(f'An error occurred while converting the file {self.__full_path}, error massage: "{e}"')
            return False
        except FileNotFoundError:
            raise FileNotFoundError(f'Make sure the path "{LYX_EXE}" is correct.')
        return False

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
