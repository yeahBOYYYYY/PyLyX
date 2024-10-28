from os.path import split, join
from PyLyX import LyX

def finder(path, fmt='pdf4'):
    file = LyX(path, None)
    file = file.load()

    test_path = join(split(path)[0], 'test.lyx')
    for obj in file[2]:
        test_file = LyX(test_path)
        test_file.write(obj)
        if not test_file.export(fmt):
            return obj
    print('Sorry, but I was not found any error.')
