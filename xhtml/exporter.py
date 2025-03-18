from os.path import splitext
from PyLyX import LyX, correct_name


def main(input_path: str, output_path: str):
    output_path = correct_name(output_path, '.xhtml')
    file = LyX(input_path)
    file.export2xhtml(output_path)


if __name__ == '__main__':
    lyx_file = input('LyX file path: ')
    xhtml_output = input('XHTML output path: ')
    xhtml_output = xhtml_output if xhtml_output else splitext(lyx_file)[0]
    main(lyx_file, xhtml_output)