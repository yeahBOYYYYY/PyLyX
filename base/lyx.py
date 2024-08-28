from os import rename, remove
from shutil import copy
from subprocess import run, CalledProcessError, TimeoutExpired
from PyLyX.base.toc import TOC
from PyLyX.base.helper import *


def __one_layout(file, line: str, current=None) -> TOC:
    start, layout, *cmd = line.split()
    text = '\n'.join(cmd)
    for line in file:
        if line == ENDS[start]:
            break

        text += line
    new = TOC(layout, text, [])

    if current is None or new.rank() <= current.rank():
        return new
    else:
        current.append(new)
        return current


def __reader(file, root: list, current=None):
    for line in file:
        if line.startswith(BEGIN_LAYOUT) or line.startswith(BEGIN_INSET):
            new = __one_layout(file, line, current)
            if new is not current:
                root.append(new)
                current = new
        elif line == BEGIN_DEEPER:
            while line != END_DEEPER:
                __reader(file, current.content())


def load(full_path: str):
    with open(full_path, 'r', encoding='utf8') as file:
        root = []
        __reader(file, root)
    return root


class LYX:
    def __init__(self, full_path: str, toc=None, template=join(CURRENT_FILE_PATH, 'template.lyx')):
        if type(toc) is list:
            for c in toc:
                if type(c) is not TOC:
                    raise TypeError(f'invalid toc: {toc}.')
        elif toc is not None and type(toc) is not TOC:
            raise TypeError(f'invalid toc: {toc}.')

        self.__full_path = correct_name(full_path, '.lyx')

        if not exists(self.__full_path):
            copy(template, self.__full_path)
        if toc is not None:
            if type(toc) is list:
                for c in toc:
                    self.write(c)
            else:
                self.write(toc)

    def line_functions(self, func, args=()):
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


    def write(self, toc: TOC):
        if exists(self.__full_path + '~'):
            remove(self.__full_path)
        with open(self.__full_path, 'r', encoding='utf8') as old:
            with open(self.__full_path + '~', 'x', encoding='utf8') as new:
                for line in old:
                    if line not in ('\\end_body\n', '\\end_document\n'):
                        new.write(line)

                new.write(str(toc))
                new.write('\n\\end_body\n\\end_document\n')

        remove(self.__full_path)
        rename(self.__full_path + '~', self.__full_path)

    def find(self, query):
        with open(self.__full_path, 'r', encoding='utf8') as f:
            for line in f:
                if query in line:
                    return True

        return False

    def find_and_replace(self, str1, str2):
        def func(line):
            return line.replace(str1, str2)

        return self.line_functions(func)

    def export(self, fmt: str, output_path=''):
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

    def reverse_hebrew_links(self):
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

    def update_version(self):
        already_updated = True
        with open(self.__full_path, 'r', encoding='utf8') as f:
            first_line = f.readline()
            if not first_line.startswith(f'#LyX {VERSION}'):
                self.export('lyx')
                already_updated = False

        if VERSION == 2.4 and not already_updated:
            self.reverse_hebrew_links()

        return not already_updated
