from xml.etree.ElementTree import Element
from PyLyX.general.helper import *


class LyXobj(Element):
    DEFAULT_RANK = 100
    NAME = 'LyXobj'
    def __init__(self, tag: str, attrib: dict, command='', category='', details='', rank=DEFAULT_RANK, text='', tail='', is_open=True):
        super().__init__(tag, attrib)
        self.__command = str(command)
        self.__category = str(category)
        self.__details = str(details)
        self.__rank = int(rank)
        self.__is_open = bool(is_open)
        self.text = str(text)
        self.tail = str(tail)

    def __str__(self):
        category = ' ' + self.__category if self.__category else ''
        details = ' ' + self.__details if self.__details else ''
        full_command = self.__command + category + details
        full_command = ' full command: ' + full_command + ',' if full_command else ''
        return f'<tag: {self.tag},{full_command} rank: {self.__rank}>'

    def can_be_nested_in(self, father):
        if type(father) in CLASSES and father.is_open():
            if self.__rank > father.__rank:
                return True
            elif father.__rank ==self.__rank == LyXobj.DEFAULT_RANK:
                return True
            else:
                return False
        else:
            return False

    def append(self, obj):
        if type(obj) in CLASSES:
            if obj.can_be_nested_in(self):
                Element.append(self, obj)
            else:
                raise Exception(f'{obj.NAME} {obj} can not be nested in this {self.NAME}: {self}.')
        else:
            raise TypeError(f'invalid {self.NAME}: {obj}.')

    def obj2lyx(self):
        return str(self)

    def open(self):
        self.__is_open = True

    def close(self):
        self.__is_open = False

    def command(self):
        return self.__command

    def category(self):
        return self.__category

    def details(self):
        return self.__details

    def rank(self):
        return self.__rank

    def is_open(self):
        return self.__is_open

    def is_close(self):
        return not self.__is_open

    def is_empty(self):
        for _ in self:
            return False
        return True

    def is_primary(self):
        return self.__rank < 0

    def is_section_title(self):
        return 0 <= self.__rank <= 6

    def is_regular(self):
        return 6 < self.__rank


class Environment(LyXobj):
    NAME = 'Environment'
    def __init__(self, command: str, category='', details='', text='', tail='', is_open=True):
        if command not in OBJECTS:
            raise TypeError(f'invalid command: {command}.')
        elif category not in OBJECTS[command]:
            raise TypeError(f'invalid category: {category}.')
        elif details not in OBJECTS[command][category]:
            raise TypeError(f'invalid details: {details}.')
        elif type(text) is not str:
            raise TypeError(f'invalid text: {text}.')
        elif type(text) is not str:
            raise TypeError(f'invalid tail: {tail}.')

        super().__init__(OBJECTS[command][category][details][TAG],
                         OBJECTS[command][category][details][ATTRIB],
                         command, category, details,
                         OBJECTS[command][category][details].get(RANK, LyXobj.DEFAULT_RANK),
                         text, tail, is_open)

    def can_be_nested_in(self, father):
        if type(father) in CLASSES and father.is_open():
            if type(father) is Section:
                if self.is_section_title() and father.is_empty() and self.rank() == father.rank():
                    return True
                else:
                    return self.rank() > father.rank()
            elif self.command() == LAYOUT:
                if self.is_regular():
                    return father.command() in {BODY, DEEPER, INSET} and father.category() != FORMULA
                elif self.is_section_title():
                    return False
                else:  # i.e. self.is_primary() == True
                    return self.rank() > father.rank()
            elif self.command() == INSET:
                return father.command() in {LAYOUT, DEEPER, INSET} and father.category() != FORMULA
            elif self.command() == DEEPER:
                return father.command() in {LAYOUT, DEEPER} and father.is_regular()
            elif self.rank() > father.rank():
                return True
            else:
                return False
        else:
            return False

    def obj2lyx(self):
        text = f'{BEGIN}{self.command()}'
        if self.category():
            text += f' {self.category()}'
        if self.details():
            text += f' {self.details()}'
        if self.category() == FORMULA and self.text.startswith(USD):
            text += f' {self.text}'
        else:
            text += f'\n{self.text}'

        for e in self:
            text += e.obj2lyx()

        text += f'{END}{self.command()}\n'
        text += self.tail
        return text


class Section(LyXobj):
    NAME = 'Section'
    def __init__(self, env: Environment, is_open=True):
        if type(env) is not Environment:
            raise TypeError(f'invalid {Environment.NAME} object: {env}.')
        elif not env.is_section_title():
            raise TypeError(f'{Environment.NAME} object {env} is not section title.')

        super().__init__(SECTION, {CLASS: env.category()}, rank=env.rank())

        self.append(env)
        if not is_open:
            self.close()

    def can_be_nested_in(self, father):
        if type(father) in CLASSES and father.is_open():
            if type(father) is Section and self.rank() > father.rank():
                return True
            elif type(father) is Environment and father.command() == BODY:
                return True
            else:
                return False
        else:
            return False

    def obj2lyx(self):
        text = ''
        for obj in self:
            text += obj.obj2lyx()
        return text


CLASSES = LyXobj.__subclasses__()
CLASSES.append(LyXobj)
