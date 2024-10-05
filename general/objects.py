from xml.etree.ElementTree import Element, tostring, indent
from PyLyX import OBJECTS, DESIGNS

ENDS = {'color': 'inherit'}


def is_known_object(command: str, category: str, details: str):
    return command in OBJECTS and category in OBJECTS[command] and details in OBJECTS[command][category]


class LyxObj(Element):
    DEFAULT_RANK = 100
    NAME = 'LyxObj'
    def __init__(self, tag, command='', category='', details='', text='', tail='', is_open=True, rank=DEFAULT_RANK):
        super().__init__(tag)
        self.text = str(text)
        self.tail = str(tail)

        self.__command = str(command)
        self.__category = str(category)
        self.__details = str(details)
        self.__rank = int(rank)
        self.__is_open = bool(is_open)

        if command + category + details:
            class_ = self.obj_props('_')
            if class_ != self.tag:
                self.set('class', class_)

    def can_be_nested_in(self, father) -> bool:
        if type(father) in CLASSES and father.is_open():
            if self.__rank > father.__rank:
                return True
            elif father.__rank == self.__rank == LyxObj.DEFAULT_RANK:
                return True

        return False

    def makeelement(self, tag='', attrib=None):
        obj = LyxObj(tag=tag)
        if attrib is not None:
            obj.attrib = attrib
        self.append(obj)

    def append(self, obj):
        if type(obj) in CLASSES:
            if self.__is_open or obj.is_deeper():
                if obj.can_be_nested_in(self):
                    Element.append(self, obj)
                else:
                    raise Exception(f'{obj.NAME} {obj} can not be nested in this {self.NAME}: {self}.')
            else:
                raise Exception(f'{self.NAME} {self} is closed.')
        else:
            raise TypeError(f'invalid {self.NAME}: {obj}.')

    def obj2lyx(self):
        if self.tag in ('table', 'th', 'tr', 'td', 'colgroup', 'col'):
            new_table = xhtml2lyxml(self)
            text = tostring(new_table, encoding='unicode')
        else:
            text = '\n' + self.start() + self.text
            for e in self:
                text += e.obj2lyx()
            text += self.end()
            text += self.tail
        d = {'&quot;': '"', '&amp;': '&', '&apos;': "'", '&lt;': '<', '&gt;': '>'}
        for key in d:
            text = text.replace(key, d[key])
        return text

    def get_dict(self):
        if is_known_object(self.__command, self.__category, self.__details):
            return OBJECTS[self.__command][self.__category][self.__details]
        else:
            return {}

    def print_lyx(self):
        print(self.obj2lyx())

    def __str__(self):
        string = self.tag
        if self.obj_props() not in (self.tag, '') :
            string += ' '
            string += self.obj_props('-')
        return f'<{self.NAME} {string}>'

    def obj_props(self, sep=' '):
        lst = []
        if self.__command:
            lst.append(self.__command)
        if self.__category:
            lst.append(self.__category)
        if self.__details:
            lst.append(self.__details)
        return sep.join(lst)

    def start(self) -> str:
        if self.is_section():
            return ''
        elif self.is_environment() and not self.is_design():
            prefix = 'begin_'
        elif self.is_design() and self.__command == 'spacing':
            prefix = 'paragraph_'
        else:
            prefix = ''
        return '\\' + prefix + self.obj_props() + '\n'

    def end(self) -> str:
        if self.is_design():
            magic_word = ENDS.get(self.__command, 'default')
            return f'\\{self.__command} {magic_word}\n'
        elif self.is_environment():
            return '\\end_' + self.__command + '\n'
        else:
            return ''

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
        return self.__command == 'layout'

    def is_inset(self):
        return self.__command == 'inset'

    def is_design(self):
        return self.__command in DESIGNS

    def is_deeper(self):
        return self.__command == 'deeper'

    def is_body(self):
        return self.__command == 'body'

    def is_document(self):
        return self.__command == 'document'

    def is_formula(self):
        return self.is_inset() and self.__category == 'formula'

    def is_standard(self):
        return self.is_layout() and self.__category == 'standard'

    def is_table_inset(self):
        return self.is_inset() and self.__category == 'table'

    def is_text(self):
        return self.is_inset() and self.__category == 'Text'

    def is_plain_layout(self):
        return self.is_layout() and (self.__category, self.__details) == ('Plain', 'Layout')


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

        if 'text' in OBJECTS[command][category][details]:
            text = OBJECTS[command][category][details]['text']
        if 'tag' in OBJECTS[command][category][details]:
            tag = OBJECTS[command][category][details]['tag']
        else:
            tag = 'div'
        super().__init__(tag, command, category, details, text, tail, is_open,
                         OBJECTS[command][category][details].get('rank', LyxObj.DEFAULT_RANK))

    def can_be_nested_in(self, father) -> bool:
        if type(father) in CLASSES:
            if self.is_deeper():
                if father.is_layout() or father.is_deeper():
                    return father.is_regular()
            elif father.is_open():
                if self.is_layout() or self.is_inset():
                    if self.is_section_title():
                        return father.is_section() and father.is_empty() and self.rank() == father.rank()
                    elif father.is_section():
                        return not father.is_empty()
                    elif father.is_formula() or father.is_standard():
                        return False
                    elif father.is_deeper():
                        return True
                    elif father.is_design():
                        return self.is_inset()
                    elif father.is_inset():
                        return father.is_text() or self.is_inset() or self.is_plain_layout()
                    elif father.is_layout():
                        return self.is_inset()
                    elif father.is_body():
                        return self.is_layout()
                    elif father.tag == 'td' or father.tag == 'th':
                        return self.is_text()
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

        super().__init__('section', rank=env.rank(), category=env.category())

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

    def obj2lyx(self):
        text = ''
        for e in self:
            text += e.obj2lyx()
        return text


CLASSES = LyxObj.__subclasses__()
CLASSES.append(LyxObj)


def xhtml2lyxml_style(cell, new_cell):
    if cell.tag == 'td':
        new_cell.set('usebox', cell.get('data-usebox'))

    style = cell.get('style')
    if style is not None:
        style = style.split('; ')
        style = [style[i].split(': ') for i in range(len(style))]
        style = dict(style)
        align = style.get('text-align')
        valign = style.get('vertiacl-align')
        if align is not None:
            new_cell.set('alignment', align)
        if valign is not None:
            new_cell.set('valignment', valign)
        for side in ('top', 'bottom', 'right', 'left'):
            value = style.get(f'border-{side}')
            if value is not None and value != 'false':
                new_cell.set(f'{side}line', 'true')

    multirow = cell.get('rowspan')
    multicolumn = cell.get('colspan')
    if multirow is not None:
        new_cell.set('rowspan', multirow)
    if multicolumn is not None:
        new_cell.set('colspan', multicolumn)


def xhtml2lyxml_cell(cell):
    new_cell = Element('cell')
    new_cell.text = cell.text
    xhtml2lyxml_style(cell, new_cell)
    for e in cell:
        if e.is_table_inset():
            new_cell.append(xhtml2lyxml(e))
        elif new_cell:
            new_cell[-1].tail += e.obj2lyx()
        else:
            new_cell.text += e.obj2lyx()
    return new_cell


def xhtml2lyxml(table: LyxObj):
    new_table = Element('lyxtabular')
    for info in {'version', 'rows', 'columns'}:
        new_table.set(info, table.get(f'data-{info}'))
    new_table.append(Element('features', {'tabularvalignment': table.get('data-tabularvalignment')}))

    for item in table:
        if item.tag == 'tr':
            new_row = Element('row')
            new_table.append(new_row)
            for cell in item:
                new_cell = xhtml2lyxml_cell(cell)
                new_row.append(new_cell)
        elif item.tag == 'colgroup':
            for col in item:
                new_col = Element('column')
                new_table.append(new_col)
                xhtml2lyxml_style(col, new_col)

    indent(new_table, space='')
    return new_table
