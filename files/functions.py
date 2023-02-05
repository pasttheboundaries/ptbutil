import os
import yaml
import json


def files_in_dir(directory_path, condition=None) -> list:
    """returns a list of file paths of all files present in the required directory.
    condition is supposed to be a callable returning bool when passed a filename"""
    condition = condition or (lambda x: True)
    filenames = os.listdir(directory_path)
    return [os.path.join(directory_path, filename) for filename in filenames if condition(filename)]


def read_yaml(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.load(f.read(), Loader=yaml.Loader)


def read_json(path, encoding='utf-8'):
    with open(path, 'r', encoding=encoding) as f:
        return json.loads(f.read())
