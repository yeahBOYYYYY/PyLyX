"""
Debug utility for finding problematic elements in LyX documents.

This module helps identify which specific element in a LyX document
is causing export failures by testing each element individually.
"""

from os.path import split, join
from PyLyX import LyX

def finder(path, fmt='pdf4'):
    """
    Find the problematic element preventing document export.
    
    Creates a test document with each element from the original document
    and attempts to export it. Returns the first element that causes
    export to fail.
    
    :param path: Path to the LyX document to debug
    :param fmt: Export format to test (default: 'pdf4')
    :return: The problematic LyX object, or None if no error found
    """
    file = LyX(path, None)
    file = file.get_doc()

    test_path = join(split(path)[0], 'test.lyx')
    for obj in file[2]:
        test_file = LyX(test_path)
        test_file.append(obj)
        if not test_file.export(fmt):
            return obj
    print('Sorry, but I was not found any error.')
