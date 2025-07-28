import pathlib
import os
from typing import Union, Optional
from itertools import chain
import datetime
import json

def files_in_dir(directory_path: str, condition: Optional[Union[callable, str]] = None, r: bool = False) -> list:
    """
    returns a list of file paths of all files present in the required directory.
    condition is supposed to be a callable returning bool when passed a filename

    directory_path: str - path of the relevant directory
    condition: callable or str for re pattern matching
    r: bool - default is False, decides if inner directories are to be searched for relevant files recurently"""

    if not isinstance(directory_path, str):
        raise TypeError('directory_path argument must be type str.')
    condition = condition or bool

    if callable(condition):
        pass
    elif isinstance(condition, str):
        pattern = condition
        condition = lambda x: pattern in x
    else:
        raise TypeError('condition parameter must be a callable or str for re pattern matching')

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


def absolute_path(path: Union[str, pathlib.Path]) -> str:
    if isinstance(path, str) and '~' in path:
        path = path.replace('~', str(pathlib.Path.home()))
    if isinstance(path, str) and path.startswith('./'):
        pass
    path = str(pathlib.Path(path).absolute())
    return path


def create_parents(path: Union[str, pathlib.Path]) -> None:
    for d in list(pathlib.Path(absolute_path(path)).parents)[::-1] + [path]:
        if os.path.isdir(d):
            pass
        else:
            os.mkdir(d)


class Instance:
    DEFAULT_DIRNAME ='_instance_'
    META_FILE = '_meta_.json'
    def __init__(self, directory: Optional[Union[str, pathlib.Path]]=None):
        directory = absolute_path(directory)
        create_parents(directory)
        self.directory = directory
        self.created = datetime.datetime.now()

        self._update_meta_file()

    def files(self):
        return files_in_dir(self.directory)

    def _update_meta_file(self):
        metafile_path = os.path.join(self.directory,  self.META_FILE)

        if os.path.isfile(metafile_path):
            with open(metafile_path, 'r') as f:
                j = json.loads(f.read())
        else:
            j = {
                'created' : self.created.isoformat(),
                }
        j['files'] = self.files()

        with open(metafile_path, 'w') as f:
            f.write(json.dumps(j))




