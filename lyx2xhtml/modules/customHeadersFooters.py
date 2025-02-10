from PyLyX.lyx2xhtml.general import CSS_FOLDER
from PyLyX.objects.Environment import Environment

def main(head: Environment, body: Environment, info: dict, css_folder=CSS_FOLDER):
    for e in body.iter():
        if e.is_category({'Right', 'Center', 'Left'}) and e.is_details({'Header', 'Footer'}):
            e.set('style', 'display: none')
