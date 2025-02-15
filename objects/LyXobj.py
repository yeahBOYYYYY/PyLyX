from copy import deepcopy
from xml.etree.ElementTree import Element
from PyLyX.data.data import OBJECTS

DEFAULT_RANK = 100


class LyXobj(Element):
    """
    Represents a LyX object with additional attributes and behaviors for
    managing hierarchical document structures.
    """

    NAME = 'LyxObj'
    def __init__(self, tag, command='', category='', details='', text='', tail='', attrib: dict | None = None, is_open=True, rank=DEFAULT_RANK):
        """
        Initializes a LyX object with specified properties.

        :param tag: XML tag name for the element.
        :param command: The first word of the element in the LyX code.
        :param category: The second word of the element in the LyX code.
        :param details: The third word of the element in the LyX code.
        :param text: Text content of the element.
        :param tail: Tail content of the element.
        :param attrib: Attributes for the XML element.
        :param is_open: Whether the element is open for appending subelements.
        :param rank: Rank of the element, element with low rank can not be subelement of higher one.
        """
        super().__init__(tag)
        self.text = str(text)
        self.tail = str(tail)
        if type(attrib) is dict:
            self.attrib = attrib
        elif attrib is not None:
            print('attrib must be a dictionary.')

        self.__command = str(command)
        self.__category = str(category)
        self.__details = str(details)
        self.__rank = int(rank)
        self.__is_open = bool(is_open)

        if command + category + details:
            self.set('class', self.obj_props_str())

    def can_be_nested_in(self, father) -> (bool, str):
        """
        Check if <self> can be subelement of <father>.

        :param father: an element for be nested in.
        :return: boolean value and message for explaining.
        """
        from PyLyX.objects.Environment import Environment, Container
        if type(father) in {LyXobj, Environment, Container}:
            if not father.is_open():
                msg = f'{father} is closed.'
                result = False
            elif self.__rank >= father.__rank or self.__rank == -DEFAULT_RANK:
                msg = ''
                result = True
            else:
                msg = f'rank {self.__rank} vs rank {father.__rank}'
                result = False
        else:
            msg = f'invalid type: {type(father)}'
            result = False
        return result, msg

    def append(self, obj):
        from PyLyX.objects.Environment import Environment, Container
        if type(obj) in {LyXobj, Environment, Container}:
            result, msg = obj.can_be_nested_in(self)
            if result:
                Element.append(self, obj)
            else:
                raise Exception(msg)
        else:
            raise TypeError(f'invalid {self.NAME}: {obj}.')

    def extend(self, objs):
        for obj in objs:
            self.append(obj)

    def insert(self, index, obj):
        from PyLyX.objects.Environment import Environment, Container
        if type(obj) in (LyXobj, Environment, Container):
            result, msg = obj.can_be_nested_in(self)
            if result:
                if index != 0 or not type(self) is Container:
                    Element.insert(self, index, obj)
                else:
                    raise Exception(f'can not change Container title.')
            else:
                raise Exception(msg)
        else:
            raise TypeError(f'invalid {self.NAME}: {obj}.')

    def __str__(self):
        string = self.obj_props_str('-')
        if not string:
            string = self.tag
        return f'<{self.NAME} {string} at {id(self)}>'

    def clear(self, save_attrib=False, save_text=False, save_tail=False):
        attrib = deepcopy(self.attrib) if save_attrib else {}
        text = self.text if save_text else ''
        tail = self.tail if save_tail else ''
        Element.clear(self)
        self.text, self.tail, self.attrib = text, tail, attrib


    def obj2lyx(self):
        code = f'\\{self.obj_props_str()}\n'
        if self.text:
            code += self.text + '\n'
        for e in self:
            code += e.obj2lyx()
        if self.tail:
            code += self.tail + '\n'
        code = xml2txt(code)
        return code


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

    def obj_props(self):
        return self.__command, self.__category, self.__details

    def rank(self):
        return self.__rank

    def is_open(self):
        return self.__is_open

    def is_section_title(self):
        return False
    
    def is_command(self, commands):
        if type(commands) is str:
            commands = commands.split()
        return self.__command in commands
    
    def is_category(self, categories):
        if type(categories) is str:
            categories = categories.split()
        return self.__category in categories

    def is_details(self, details):
        if type(details) is str:
            details = details.split()
        return self.__details in details

    def obj_props_str(self, sep=' '):
        props = list(self.obj_props())
        while props and not props[-1]:
            props.pop()
        return sep.join(props)

    def get_dict(self):
        if self.is_in():
            return OBJECTS[self.__command][self.__category][self.__details]
        else:
            return {}

    def is_in(self, dictionary=None):
        dictionary = OBJECTS if dictionary is None else dictionary
        if self.__command in dictionary:
            if self.__category in dictionary[self.__command]:
                if self.__details in dictionary[self.__command][self.__category]:
                    return True

        return False

    def copy(self):
        from PyLyX.objects.Environment import Environment, Container
        if type(self) is Environment:
            return Environment(self.command(), self.category(), self.details(), self.text, self.tail, self.attrib, self.is_open())
        elif type(self) is Container:
            return Container(self[0], self.is_open())
        else:
            return LyXobj(self.tag, self.command(), self.category(), self.details(), self.text, self.tail, self.attrib, self.is_open(), self.rank())


def xml2txt(text: str):
    dictionary = {'quot;': '"', 'amp;': '&', 'apos;': "'", 'lt;': '<', 'gt;': '>'}
    for key in dictionary:
        text = text.replace('&' + key, dictionary[key])
        text = text.replace(key, dictionary[key])
    return text
