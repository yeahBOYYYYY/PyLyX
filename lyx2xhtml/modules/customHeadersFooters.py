from PyLyX.objects.Environment import Environment

def main(head: Environment, body: Environment, info: dict):
    for e in body.iter():
        if e.is_category({'Right', 'Center', 'Left'}) and e.is_details({'Header', 'Footer'}):
            e.set('style', 'display: none')
