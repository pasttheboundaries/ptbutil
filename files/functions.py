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


def nowfilename(prefix=None, suffix=None, extension=None, timeformat=None, cputime=False):
    """
    returns a name of a data with time signature
    name format is [prefix][time-signature][suffix].[extension]
    :param prefix: str
    :param suffix: str
    :param extension: str
    :param timeformat: str (according to time.strftime protocol)
    :param cputime: bool - if True uses cpu time instead of formatted time
    :return: str
    """
    prefix = prefix or ''
    suffix = suffix or ''
    extension = extension or ''
    if extension:
        extension = '.' + extension
    timeformat = timeformat or '%Y%m%dT%H%M'
    if cputime:
        t = str(time.process_time()).replace('.', '')
    else:
        t = time.strftime(timeformat, time.localtime())
    return ''.join((prefix, t, suffix, extension))


def read_yaml(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.load(f.read(), Loader=yaml.Loader)


def read_json(path, encoding='utf-8'):
    with open(path, 'r', encoding=encoding) as f:
        return json.loads(f.read())


def timed_filename(prefix=None, suffix=None, extension=None, timeformat=None):
    """
    creates data name with a time-stamp
    the time-stamp format can be declared as per time library protocol
    if not declared the default format is : %Y%m%dT%H%M'

    :param prefix: str
    :param suffix: str
    :param extension: str
    :param timeformat: as per time library protocol
    :return: str
    """

    prefix = prefix or ''
    suffix = suffix or ''
    extension = extension or ''
    if extension:
        extension = '.' + extension
    timeformat = timeformat or '%Y%m%dT%H%M'
    t = time.strftime(timeformat,time.localtime())
    return ''.join((prefix, t, suffix, extension))
