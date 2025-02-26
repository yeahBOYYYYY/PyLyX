from os.path import splitext
from sys import argv
from PyLyX import LyX, correct_name


def main(input_path: str, output_path: str):
    output_path = correct_name(output_path, '.xhtml')
    file = LyX(input_path)
    file.export2xhtml(output_path)


if __name__ == '__main__':
    if len(argv) > 1:
        lyx_file = argv[1]
        xhtml_output = argv[2] if len(argv) > 2 else splitext(lyx_file)[0]
        main(lyx_file, xhtml_output)
    else:
        print('please give a LyX file.')