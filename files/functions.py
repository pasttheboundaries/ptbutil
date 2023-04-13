import os
import yaml
import json
from itertools import chain
from typing import Optional


def files_in_dir(directory_path: str, condition: Optional[callable] = None, r: bool = False) -> list:
    """
    returns a list of file paths of all files present in the required directory.
    condition is supposed to be a callable returning bool when passed a filename

    directory_path: str - path of the relevant directory
    condition: callable
    r: bool - default is False, decides if inner directories are to be searched for relevant files recurently"""

    if not isinstance(directory_path, str):
        raise TypeError('directory_path argument must be type str.')
    condition = condition or bool
    if not callable(condition):
        raise TypeError('condition parameter must be a callable')
    r = bool(r)

    filenames = os.listdir(directory_path)
    relevant_files = [os.path.join(directory_path, filename) for filename in filenames if condition(filename)]
    if not r:
        return relevant_files

    inner_dirs = [os.path.join(directory_path, dirname) for dirname in os.listdir(directory_path)]
    inner_dirs = [inner_dir for inner_dir in inner_dirs if os.path.isdir(inner_dir)]
    inner_files = list(chain(*(files_in_dir(innerdir, condition=condition, r=r)for innerdir in inner_dirs)))
    relevant_files.extend(inner_files)

    return relevant_files


def read_yaml(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.load(f.read(), Loader=yaml.Loader)


def read_json(path, encoding='utf-8'):
    with open(path, 'r', encoding=encoding) as f:
        return json.loads(f.read())
