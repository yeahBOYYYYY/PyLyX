from xml.etree.ElementTree import Element
from PyLyX.helper import *

DEFAULT_RANK = 100


class LyXobj(Element):
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
        category = ' ' + self.__details if self.__details else ''
        details = ' ' + self.__details if self.__details else ''
        full_command = self.__command + category + details
        full_command = ' full command: ' + full_command + ',' if full_command else ''
        return f'<tag: {self.tag},{full_command} rank: {self.__rank}>'

    def can_be_nested_in(self, father):
        return type(father) in CLASSES and (self.__rank == DEFAULT_RANK or self.__rank > father.__rank)

    def append(self, obj):
        if type(obj) in CLASSES:
            if self.is_open():
                if obj.can_be_nested_in(self):
                    Element.append(self, obj)
                else:
                    raise Exception(f'LyXobj {obj} can not be nested in LyXobj: {self}.')
            else:
                raise Exception(f'this LyXobj is closed: {self}.')
        else:
            raise TypeError(f'invalid LyXobj: {obj}.')

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
            return True
        return False


class Environment(LyXobj):
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
                         OBJECTS[command][category][details][ATTRIB], command, category, details,
                         OBJECTS[command][category][details].get(RANK, DEFAULT_RANK), text, tail, is_open)

    def can_be_nested_in(self, father):
        if type(father) is Section:
            if self.is_section_title() and not father.is_empty() and self.rank() == father.rank():
                return True
            else:
                return self.rank() > father.rank()
        elif type(father) is not Environment or not father.is_open():
            return False
        elif self.command() == LAYOUT:
            if self.is_regular():
                return father.command() in {BODY, DEEPER, INSET}
            elif self.is_section_title():
                return False
            else:  # i.e. self.is_primary() == True
                return self.rank() > father.rank()
        elif self.command() == INSET:
            return father.command() in {LAYOUT, DEEPER, INSET}
        elif self.command() == DEEPER:
            return father.command() in {LAYOUT, DEEPER} and father.is_regular()
        elif self.rank() > father.rank():
            return True
        else:
            return False

    def obj2lyx(self):
        text = f'{BEGIN}{self.command()}'
        if self.category():
            text += f' {self.category()}'
        if self.details():
            text += f' {self.details()}'
        text += f'\n{self.text}'

        for e in self:
            text += e.obj2lyx()

        text += f'{END}{self.command()}\n'
        text += self.tail
        return text

    def is_primary(self):
        return self.rank() < 0

    def is_section_title(self):
        return 0 <= self.rank() <= 6

    def is_regular(self):
        return 6 < self.rank()


class Section(LyXobj):
    def __init__(self, env: Environment, is_open=True):
        if type(env) is not Environment:
            raise TypeError(f'invalid Environment object: {env}.')
        elif not env.is_section_title():
            raise TypeError(f'Environment object {env} is not section title.')

        super().__init__(SECTION, {}, rank=env.rank())

        self.append(env)
        if not is_open:
            self.close()

    def can_be_nested_in(self, father):
        return type(father) is Section and self.rank() > father.rank()

    def obj2lyx(self):
        text = ''
        for obj in self:
            text += obj.obj2lyx()
        return text


class Design(LyXobj):
    def __init__(self, key_word: str, choice: str, details='', is_open=True):
        if key_word not in KEY_WORDS:
            raise TypeError(f'invalid key word: {key_word}.')
        elif choice not in KEY_WORDS[key_word]:
            raise TypeError(f'invalid choice: {choice} (in {key_word}).')

        super().__init__(KEY_WORDS[key_word][choice][self.__details][TAG], {}, key_word, choice, details, is_open=is_open)

    def obj2lyx(self):
        text = self.command()
        if self.category():
            text += f' {self.category()}'
        if self.details():
            text += f' {self.details()}'

        for obj in self:
            text += obj.obj2lyx()

        text += f'{self.command()} default\n\n'
        return text


CLASSES = {LyXobj, Environment, Section, Design}
