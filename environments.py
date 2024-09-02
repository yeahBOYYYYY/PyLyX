from xml.etree.ElementTree import Element
from PyLyX.helper import *

DEFAULT_RANK = 100


class Object(Element):
    def __init__(self, tag: str, attrib: dict, command='', category='', details='', rank=DEFAULT_RANK, text='', tail='', is_open=True):
        Element.__init__(self, tag, attrib)
        self.__command = str(command)
        self.__category = str(category)
        self.__details = str(details)
        self.__rank = int(rank)
        self.__is_open = bool(is_open)
        self.text = str(text)
        self.tail = str(tail)

    def can_be_nested_in(self, father):
        return type(father) is object and (self.__rank == DEFAULT_RANK or self.__rank > father.__rank)

    def env2lyx(self):
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


class Environment(Object):
    def __init__(self, command: str, category='', details='', text='', tail='', is_open=True):
        if command not in ENVIRONMENTS:
            raise TypeError(f'invalid command: {command}.')
        elif category not in ENVIRONMENTS[command]:
            raise TypeError(f'invalid category: {category}.')
        elif details not in ENVIRONMENTS[command][category]:
            raise TypeError(f'invalid details: {details}.')
        elif type(text) is not str:
            raise TypeError(f'invalid text: {text}.')
        elif type(text) is not str:
            raise TypeError(f'invalid tail: {tail}.')

        Object.__init__(self, ENVIRONMENTS[command][category][details][TAG],
                        ENVIRONMENTS[command][category][details][ATTRIB],
                        command, category, details,
                        ENVIRONMENTS[command][category][details].get(RANK, DEFAULT_RANK),
                        text, tail, is_open)

    def can_be_nested_in(self, father):
        if type(father) is Section:
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

    def append(self, element):
        if self.is_open():
            if type(element) in {Environment, Design}:
                if element.can_be_nested_in(self):
                    Element.append(self, element)
                else:
                    raise Exception('element can not be nested in this Environment object.')
            else:
                raise TypeError(f'invalid Environment object: {element}.')
        else:
            raise Exception(f'this Environment object is closed: {self}.')

    def env2lyx(self):
        text = f'{BEGIN}{self.command()}'
        if self.category():
            text += f' {self.category()}'
        if self.details():
            text += f' {self.details()}'
        text += f'\n{self.text}'

        for e in self:
            text += e.env2lyx()

        text += f'{END}{self.command()}\n'
        text += self.tail
        return text

    def is_primary(self):
        return self.rank() < 0

    def is_section_title(self):
        return 0 <= self.rank() <= 6

    def is_regular(self):
        return 6 < self.rank()


class Section(Object):
    def __init__(self, env: Environment, is_open=True):
        if type(env) is not Environment:
            raise TypeError(f'invalid Environment object: {env}.')
        elif not 0 <= env.rank() <= 6:
            raise TypeError(f'Environment object {env} is not section title.')

        Object.__init__(self, SECTION, {}, rank=-1)

        self.append(env)
        self.__rank = env.rank()
        self.__is_open = is_open

    def can_be_nested_in(self, father):
        return type(father) is Section and self.rank() > father.rank()

    def append(self, element):
        if type(element) in {Environment, Section, Design}:
            if element.rank() > self.rank():
                Element.append(self, element)
            else:
                raise Exception('element can not be nested in this Section object.')
        else:
            raise TypeError(f'invalid Environment object: {element}.')

    def env2lyx(self):
        text = ''
        for e in self:
            text += e.env2lyx()
        return text


class Design(Object):
    def __init__(self, key_word: str, choice: str, details='', is_open=True):
        if key_word not in KEY_WORDS:
            raise TypeError(f'invalid key word: {key_word}.')
        elif choice not in KEY_WORDS[key_word]:
            raise TypeError(f'invalid choice: {choice} (in {key_word}).')

        Object.__init__(self, KEY_WORDS[key_word][choice][self.__details][TAG],
                        {}, key_word, choice, details, is_open=is_open)

    def env2lyx(self):
        text = self.command()
        if self.category():
            text += f' {self.category()}'
        if self.details():
            text += f' {self.details()}'

        for e in self:
            text += e.env2lyx()

        text += f'{self.command()} default\n\n'
        return text
