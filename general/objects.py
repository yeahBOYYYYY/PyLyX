from xml.etree.ElementTree import Element
from PyLyX.general.helper import *


ENDS = {'on': 'off'}


class LyxObj(Element):
    DEFAULT_RANK = 100
    NAME = 'LyxObj'
    def __init__(self, command='', category='', details='', text='', tail='', is_open=True, rank=DEFAULT_RANK, tag=None):
        if type(self) is Environment and TAG in OBJECTS[command][category][details]:
            tag = OBJECTS[command][category][details][TAG]
        elif tag is None:
            tag = DIV

        super().__init__(tag)
        self.set(CLASS, (category + details).lower())
        self.text = str(text)
        self.tail = str(tail)

        self.__command = str(command)
        self.__category = str(category)
        self.__details = str(details)
        self.__rank = int(rank)
        self.__is_open = bool(is_open)

    def __str__(self):
        category = ' ' + self.__category if self.__category else ''
        details = ' ' + self.__details if self.__details else ''
        return self.__command + category + details

    def __get_item__(self, items):
        if type(items) is int:
            return self[items + 1]
        else:
            return self[items]

    def can_be_nested_in(self, father) -> bool:
        if type(father) in CLASSES and father.is_open():
            if self.__rank > father.__rank:
                return True
            elif father.__rank ==self.__rank == LyxObj.DEFAULT_RANK:
                return True

        return False

    def append(self, obj):
        if type(obj) in CLASSES:
            if obj.can_be_nested_in(self):
                Element.append(self, obj)
            else:
                raise Exception(f'{obj.NAME} {obj} can not be nested in this {self.NAME}: {self}.')
        else:
            raise TypeError(f'invalid {self.NAME}: {obj}.')

    def start(self) -> str:
        if self.is_environment() and not self.is_design():
            return BEGIN + str(self) + '\n'
        elif self.is_section():
            return ''
        else:
            return '\\' + str(self) + '\n'

    def end(self) -> str:
        if self.is_design():
            magic_word = ENDS[self.__category] if self.__category in ENDS else DEFAULT
            return f'\\{self.__command} {magic_word}\n'
        elif self.is_environment():
            return f'{END}{self.__command}\n'
        else:
            return ''

    def obj2lyx(self):
        text = self.start() + self.text + '\n'

        for e in self:
            text += e.obj2lyx()

        text += self.end()
        text += self.tail
        return text

    def open(self):
        self.__is_open = True

    def close(self):
        #  todo: check all required
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

    def is_section(self):
        return type(self) is Section

    def is_environment(self):
        return type(self) is Environment

    def is_primary(self):
        return self.__rank < 0

    def is_section_title(self):
        return self.is_environment() and 0 <= self.__rank <= 6

    def is_regular(self):
        return 6 < self.__rank

    def is_layout(self):
        return self.__command == LAYOUT

    def is_inset(self):
        return self.__command == INSET

    def is_design(self):
        return self.__command in DESIGNS

    def is_deeper(self):
        return self.__command == DEEPER

    def is_body(self):
        return self.__command == BODY

    def is_formula(self):
        return self.is_inset() and self.__category == FORMULA

    def is_standard(self):
        return self.is_layout() and self.__category == STANDARD

    def is_table(self):
        return self.is_inset() and self.__category == TABLE


class Environment(LyxObj):
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

        if TEXT in OBJECTS[command][category][details]:
            text = OBJECTS[command][category][details][TEXT]
        super().__init__(command, category, details, text, tail, is_open,
                         OBJECTS[command][category][details].get(RANK, LyxObj.DEFAULT_RANK))

    def can_be_nested_in(self, father) -> bool:
        if type(father) in CLASSES and father.is_open():
            if self.is_layout() or self.is_inset():
                if father.is_section():
                    if self.is_section_title():
                        return father.is_empty() and self.rank() == father.rank()
                elif father.is_formula() or father.is_standard():
                    return False
                elif father.is_inset() or father.is_deeper():
                    return True
                elif father.is_layout():
                    return self.is_inset()
                elif father.is_body():
                    return self.is_layout()
            elif self.is_deeper():
                if father.is_layout() or father.is_deeper():
                    return father.is_regular()
            elif self.is_design():
                return father.is_layout() or father.is_inset()
            elif self.is_primary():
                return self.rank() > father.rank()

        return False


class Section(LyxObj):
    NAME = 'Section'
    def __init__(self, env: Environment, is_open=True):
        if type(env) is not Environment:
            raise TypeError(f'invalid {Environment.NAME} object: {env}.')
        elif not env.is_section_title():
            raise TypeError(f'{Environment.NAME} object {env} is not section title.')

        super().__init__(tag=SECTION, rank=env.rank(), category=env.category())

        self.append(env)
        if not is_open:
            self.close()

    def can_be_nested_in(self, father):
        if type(father) in CLASSES and father.is_open():
            if father.is_section() and self.rank() > father.rank():
                return True
            elif father.is_body():
                return True

        return False


class TableObj(LyxObj):
    def __init__(self):
        super().__init__()


CLASSES = LyxObj.__subclasses__()
CLASSES.append(LyxObj)
