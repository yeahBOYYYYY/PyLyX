from PyLyX.base.helper import *


class TOC:
    def __init__(self, layout: str, text, content: list):
        if layout not in LAYOUTS:
            raise TypeError(f'invalid layout: {layout}.')
        elif type(text) is not str and not is_table(text):
            raise TypeError(f'invalid title: {text}.')
        elif type(content) is not list:
            raise TypeError(f'invalid content: {content}.')

        for i in range(len(content)):
            if type(content[i]) is TOC:
                continue
            content[i] = TOC(*content[i])

        self.__layout = layout
        self.__text = text
        self.__content = content
        self.__rank = SECTION_LAYOUTS[layout][RANK] if layout in SECTION_LAYOUTS else 10

    def layout(self):
        return self.__layout

    def text(self):
        return self.__text.copy()

    def content(self):
        return self.__content.copy()

    def rank(self):
        return self.__rank

    def append(self, item):
        if type(item) is str or type(item) is TOC:
            self.__content.append(item)
        else:
            raise TypeError('Content must be string or TOC only.')

    def __str__(self):
        if type(self.__text) is str:
            text = self.__text
        else:
            text = create_table(self.__text)

        for toc in self.__content:
            text += str(toc)

        return create_layout(self.__layout, text)

    def __len__(self):
        return len(self.__content)

    def __iter__(self):
        self.cur = 0
        return self

    def __next__(self):
        if self.cur < len(self.__content):
            result = self.__content[self.cur]
            self.cur += 1
            return result
        else:
            raise StopIteration

    def __getitem__(self, item):
        return self.__content[item]

    def __bool__(self):
        return self.__text or self.__content
