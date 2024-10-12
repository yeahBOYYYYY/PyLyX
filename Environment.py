from PyLyX import OBJECTS, DESIGNS, PAR_SET, ENDS, xml2txt
from PyLyX.LyXobj import LyXobj, DEFAULT_RANK


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

        rank = OBJECTS[command][category][details].get('rank', DEFAULT_RANK)
        if command == 'backslash' or category == 'space':
            is_open = False
        super().__init__(command, command, category, details, text, tail, {}, is_open, rank)

    def can_be_nested_in(self, father) -> bool:
        if type(father) not in (LyXobj, Environment, Container):
            return False
        elif not father.is_open():
            return False
        elif self.is_command('deeper'):
            return type(father) is Container and father.rank() > 6 and not father.is_command('Standard')
        elif self.is_command('layout') or self.is_command('inset'):
            if self.is_section_title():
                return type(father) is Container and not bool(father) and self.rank() == father.rank()
            elif type(father) is Container:
                if father:
                    return True
                else:
                    return self.rank() == father.rank() and self.obj_props() == father.obj_props()
            elif father.is_category('Formula'):
                return False
            elif father.is_command('deeper'):
                return True
            elif father.is_command('layout') or father.command() in DESIGNS or father.command() in PAR_SET:
                return self.is_command('inset')
            elif father.is_command('inset'):
                if self.obj_props() != father.obj_props():
                    return father.is_category('Text') or self.is_command('inset') or (self.is_category('Plain') and self.details() == 'Layout')
            elif father.is_command('body'):
                return self.is_command('layout')
            elif father.tag == 'cell':
                return self.is_category('Text')
        elif self.tag == 'lyxtabular':
            return father.is_category('Tabular')
        elif self.command() in DESIGNS:
            return father.is_command('layout') or father.is_command('inset') or father.command() in DESIGNS
        elif self.command() in PAR_SET:
            return father.is_command('layout')
        elif self.rank() < 0:
            return self.rank() > father.rank()
        else:
            return False

    def obj2lyx(self, to_end=True):
        text = ''
        if self.is_category('Formula') and self.text.startswith('$'):
            text += f'\\begin_{self.obj_props()} '
        elif self.command() in DESIGNS or self.command() in PAR_SET:
            text += f'\\{self.obj_props()}\n'
        else:
            text += f'\\begin_{self.obj_props()}\n'

        if 'required' in self.get_dict():
            text += perform_required(self)

        if self.text:
            text += self.text + '\n'

        if self:
            for i in range(len(self) - 1):
                text += self[i].obj2lyx()
            text += self[-1].obj2lyx(False)

        if self.command() in DESIGNS:
            if to_end or self.tail:
                magic_word = ENDS['usually'].get(self.command(), 'default')
                if magic_word:
                    text += f'\\{self.command()} {magic_word}\n'
        elif self.command() not in PAR_SET:
            text += f'\\end_{self.command()}\n\n'

        if self.tail:
            text += self.tail

        text = xml2txt(text)
        return text + '\n'

    def is_section_title(self):
        return 0 <= self.rank() <= 6


class Container(LyXobj):
    NAME = 'Container'
    def __init__(self, env: Environment, is_open=True):
        if type(env) is not Environment:
            raise TypeError(f'invalid {Environment.NAME} object: {env}.')
        elif not env.is_command('layout'):
            raise TypeError(f'{Environment.NAME} object {env} is not layout obj.')

        super().__init__('container', env.command(), env.category(), env.details(), rank=env.rank())

        self.append(env)
        if not is_open:
            self.close()

    def can_be_nested_in(self, father):
        if type(father) not in (LyXobj, Environment, Container):
            return False
        elif not father.is_open:
            return False
        elif type(father) is Container or father.is_command('deeper'):
            return self.rank() > father.rank() or self.rank() == DEFAULT_RANK
        elif father.is_command('body'):
            return True

        return False

    def obj2lyx(self, is_not_last=True):
        text = ''
        for e in self:
            text += e.obj2lyx()
        text = xml2txt(text)
        return text


def perform_required(obj: Environment):
    lst1, lst2 = obj.get_dict().get('required', []), obj.get_dict().get('optional', [])
    lst = lst1 + lst2
    text = ''
    for command in lst:
        if command in lst1 and not command in obj.attrib:
            for key in obj.attrib:
                new_commands = obj.attrib[key].split(command, maxsplit=1)
                if len(new_commands) == 2:
                    obj.attrib[key], obj.attrib[command] = new_commands
                    return perform_required(obj)
            else:
                raise Exception(f'command {command} is missed in {obj}.\nattributes: {obj.attrib},')
        elif command in obj.attrib:
            text += f'{command} {obj.get(command)}\n'
    return text
