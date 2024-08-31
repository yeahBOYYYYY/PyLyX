from xml.etree.ElementTree import Element
from PyLyX.helper import *


DEFAULT_RANK = 100


class Environment(Element):
    def __init__(self, command: str, category='', text='', tail='', details='', is_open=True):
        if command not in COMMANDS:
            raise TypeError(f'invalid command: {command}.')
        elif category not in COMMANDS[command]:
            raise TypeError(f'invalid category: {category}.')
        elif details not in COMMANDS[command][category]:
            raise TypeError(f'invalid details: {details}.')
        elif type(text) is not str:
            raise TypeError(f'invalid text: {text}.')
        elif type(text) is not str:
            raise TypeError(f'invalid tail: {tail}.')

        Element.__init__(self, COMMANDS[command][category][details][TAG],
                         COMMANDS[command][category][details][ATTRIB])
        self.text = text
        self.tail = tail

        self.__command = command
        self.__category = category
        self.__details = details
        self.__rank = COMMANDS[command][category][details].get(RANK, DEFAULT_RANK)
        self.__is_open = is_open

    def command(self):
        return self.__command

    def category(self):
        return self.__category

    def details(self):
        return self.__details

    def rank(self):
        return self.__rank

    def is_section(self):
        return COMMANDS[self.__command][self.__category][self.__details][TAG] == 'section'

    def is_open(self):
        return self.__is_open

    def open(self):
        self.__is_open = True

    def close(self):
        self.__is_open = False

    def can_be_nested_in(self, toc):
        if type(toc) is not Environment or not toc.__is_open:
            return False
        elif toc.is_section() and (self.rank() > toc.rank() or 0 <= self.__rank <= 6):
            return True
        elif ((toc.__command == DEEPER and self.__rank > 6) or
              (toc.__rank > 6 and self.__command == DEEPER)):
            return True
        elif ((toc.__command == INSET and self.__command == LAYOUT) or
              (self.__command == INSET and toc.__command == LAYOUT and toc.__rank > 6)):
            return True
        elif self.__rank > toc.__rank:
            return True
        else:
            return False

    def append(self, item):
        if self.__is_open:
            if type(item) is Environment:
                if item.can_be_nested_in(self):
                    if self.is_section() and self.__rank == DEFAULT_RANK:
                        self.__rank = item.__rank
                    Element.append(self, item)
                else:
                    raise Exception('item can not be nested in this Environment object.')
            else:
                raise TypeError('item must be Environment object.')
        else:
            raise Exception('this Environment object is closed.')

    def __str__(self):
        text = ''

        if not self.is_section():
            text += f'{BEGIN}{self.__command}'
            if self.__category:
                text += f' {self.__category}'
            if self.__details:
                text += f' {self.__details}'
            text += f'\n{self.text}\n'

        for t in self:
            text += str(t)

        if not self.is_section():
            text += f'{END}{self.__command}\n\n'
            text += self.tail

        return text
