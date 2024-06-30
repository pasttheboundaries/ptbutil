"""
This is an ad-hoc text depo
TexcDepo class uses a single argument - direcory path to deposit textfiles
it has 4 methods:
write - writes text file
write_many - writes multiple text files
read - reads a text file
read_many - return a generator with documents
"""

import pathlib
import os
from typing import Union, Optional, Iterable, Callable
from collections.abc import Iterable as IterableType
from ptbutil.files.functions import absolute_path, nowfilename
from ptbutil.validation.types import validate_type


class TextDepo:
    def __init__(self,
                 dir_path: Union[str, pathlib.Path],
                 file_name: Optional = None,
                 encoding='utf-8'):
        self.dir_path = absolute_path(dir_path)
        self.file_name = file_name
        self.encoding = encoding

    def write(self, text: str):
        validate_type(text, str, error_message='TextDepo can only write type str.')
        file_name = nowfilename(prefix=self.file_name, cputime=True, extension='txt')
        with open(file_name, 'w', encoding=self.encoding) as f:
            f.write(text)

    def write_many(self, texts: Iterable):
        validate_type(texts, IterableType, error_message='Method write_many accepts Iterable type only.')
        for t in texts:
            self.write(t)

    def read(self,
             filename: Optional[str] = None,
             condition: Optional[Union[Callable, str]] = None):
        if not (filename or condition):
            raise ValueError('Expected one of arguments: filename or condition')
        if filename:
            file_path = os.path.join(self.dir_path, filename)
            with open(file_path, 'r', encoding=self.encoding) as f:
                return f.read()
        else:
            if isinstance(condition, str):
                condition = lambda x: condition in x
            files = os.listdir(self.dir_path)
            files = (f for f in files if f.endswith('txt') and condition(f))
            if files:
                return files[0]
            else:
                return None

    def read_many(self, condition: Union[Callable, str]):
        if isinstance(condition, str):
            condition = lambda x: condition in x
        files = os.listdir(self.dir_path)
        files = (f for f in files if f.endswith('txt') and condition(f))
        for f in files:
            yield self.read(f)
