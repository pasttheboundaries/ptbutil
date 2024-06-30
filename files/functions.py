import json
import os
import pathlib

from itertools import chain
from typing import Optional, Union

import time
import yaml


def absolute_path(path: Union[str, pathlib.Path]) -> str:
    if isinstance(path, str) and '~' in path:
        path = path.replace('~', str(pathlib.Path.home()))
    if isinstance(path, str) and path.startswith('./'):
        pass
    path = str(pathlib.Path(path).absolute())
    return path


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
    filenames = [os.path.join(directory_path, filename) for filename in filenames]
    filenames = [f for f in filenames if condition(f)]
    filenames = [f for f in filenames if os.path.isfile(f)]
    if not r:
        return filenames

    inner_dirs = [os.path.join(directory_path, dirname) for dirname in os.listdir(directory_path)]
    inner_dirs = [inner_dir for inner_dir in inner_dirs if os.path.isdir(inner_dir)]
    inner_files = list(chain(*(files_in_dir(innerdir, condition=condition, r=r)for innerdir in inner_dirs)))
    filenames.extend(inner_files)

    return filenames


class UniqueAdnex(object):
    """
    this is a helper object of a timestampped_filename function
    """
    def __init__(self):
        self.pm = 0
        self.t = None

    def __call__(self, t):
        if t == self.t:
            self.pm += 1
            return self.pm
        else:
            self.t = t
            self.pm = 0
            return self.pm

formated_ua = UniqueAdnex()
monotonic_ua = UniqueAdnex()


def timestampped_filename(prefix=None, suffix=None, extension=None, timeformat=None, adnex_sep='p'):
    """
    returns a name of a data with time signature
    name format is [prefix][time-signature][suffix].[extension]
    :param prefix: str
    :param suffix: str
    :param extension: str
    :param timeformat: str (according to time.strftime protocol) if None a time.monotonic will be used
    :param adnex_sep: str - uniqe adnex separator
    :return: str
    """
    prefix = prefix or ''
    suffix = suffix or ''
    extension = extension or ''
    if extension:
        extension = '.' + extension
    if timeformat:
        t = time.strftime(timeformat, time.localtime())
        t = t + adnex_sep + str(formated_ua(t))
    else:
        t = str(time.monotonic_ns()).replace('.', '')
        t = t + adnex_sep + str(monotonic_ua(t))

    return ''.join((prefix, t, suffix, extension))


nowfilename = timestampped_filename  # alias

def read_yaml(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.load(f.read(), Loader=yaml.Loader)


def read_json(path, encoding='utf-8'):
    with open(path, 'r', encoding=encoding) as f:
        return json.loads(f.read())


