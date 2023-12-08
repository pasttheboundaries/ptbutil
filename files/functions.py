import json
import os
from itertools import chain
from typing import Optional

import time
import yaml


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



def nowfilename(prefix=None, suffix=None, extension=None, timeformat=None, cputime=False):
    """
    returns a name of a file with time signature
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
    t = (not cputime) and time.strftime(timeformat, time.localtime() or str(time.process_time())).replace('.', '')
    return ''.join((prefix, t, suffix, extension))

def read_yaml(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.load(f.read(), Loader=yaml.Loader)


def read_json(path, encoding='utf-8'):
    with open(path, 'r', encoding=encoding) as f:
        return json.loads(f.read())


def timed_filename(prefix=None, suffix=None, extension=None, timeformat=None):
    """
    creates file name with a time-stamp
    the time-stamp format can be declared as per time library protocol
    if not declared the default format is : %Y%m%dT%H%M'

    :param prefix: str
    :param suffix: str
    :param extension: str
    :param timeformat: as per time library protocol
    :return: str
    """

    prefix = prefix or ''
    suffix =suffix or ''
    extension = extension or ''
    if extension:
        extension = '.' + extension
    timeformat = timeformat or '%Y%m%dT%H%M'
    t = time.strftime(timeformat,time.localtime())
    return ''.join((prefix, t, suffix, extension))
