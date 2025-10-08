"""
Helper utilities for the PyLyX package.

This module provides utility functions for:
- File path and extension handling
- Language detection (Hebrew, English)
- Text bracket correction for different LyX versions
"""

from os.path import split, splitext, join
from string import ascii_letters
from PyLyX.objects.LyXobj import LyXobj


def correct_name(full_path: str, extension: str) -> str:
    """
    Ensure a file path has the correct extension.
    
    Strips existing extension and adds the specified one.
    
    :param full_path: File path (with or without extension)
    :param extension: Desired extension (with or without leading dot)
    :return: Path with correct extension
    """
    extension = extension if extension.startswith('.') else '.' + extension
    path, name = split(full_path)
    name = splitext(name)[0]
    path = join(path, name + extension)
    return path


def default_path(old_path, new_extension, new_path=''):
    """
    Get output path with new extension.
    
    If new_path is provided, uses it; otherwise converts old_path extension.
    
    :param old_path: Original file path
    :param new_extension: New extension to use
    :param new_path: Optional explicit new path
    :return: Path with new extension
    """
    if new_path:
        return correct_name(new_path, new_extension)
    else:
        return correct_name(old_path, new_extension)


def detect_lang(text: str):
    """
    Detect the language of text based on character set.
    
    Checks for Hebrew or English characters.
    
    :param text: Text to analyze
    :return: 'hebrew', 'english', or empty string if undetermined
    """
    for char in text:
        if char in 'אבגדהוזחטיכלמנסעפצקרשת':
            return 'hebrew'
        elif char in ascii_letters:
            return 'english'
    return ''


def correct_brackets(text: str, is_open=False):
    """
    Correct bracket direction for different LyX format versions.
    
    Some LyX versions require bracket normalization for proper parsing.
    
    :param text: Text containing brackets
    :param is_open: Whether a bracket pair is currently open
    :return: Tuple of (corrected_text, new_is_open_state)
    """
    new_text = ''
    for brackets in {{'(', ')'}, {'[', ']'}, {'{', '}'}}:
        for char in text:
            if char in brackets:
                if is_open:
                    new_text += ')'
                else:
                    new_text += '('
                is_open = not is_open
            else:
                new_text += char
    return new_text, is_open


def run_correct_brackets(obj: LyXobj):
    """
    Apply bracket correction to an entire LyX object tree.
    
    Iterates through all elements and corrects brackets in text and tail,
    skipping formula content.
    
    :param obj: Root LyX object to process
    """
    is_open = False
    for e in obj.iter():
        if not e.is_category({'Formula', 'FormulaMacro'}):
            e.text , is_open = correct_brackets(e.text, is_open)
        e.tail, is_open = correct_brackets(e.tail, is_open)
