"""
TextDepo: A module for managing text storage and retrieval.

This module provides a TextDepo class for storing and retrieving text files
in a specified directory. It includes functionality for writing single or
multiple texts, reading files based on filename or conditions, and maintaining
an index of stored files.

Classes:
    TextDepoIndex: A subclass of QuickStore for managing the file index.
    FileDescriptor: A dataclass for storing file metadata.
    TextDepo: The main class for text storage and retrieval operations.

Functions:
    textdepo_hash: Generates a hash for a given text.

Dependencies:
    pathlib, os, time, dataclasses, typing, collections.abc, hashlib,
    ptbutil.files.functions, ptbutil.validation.types, ptbutil.store.quickstore
"""


import pathlib
import os
import time
from dataclasses import dataclass
from typing import Union, Optional, Iterable, Callable, Generator, Any
from collections.abc import Iterable as IterableType
from hashlib import sha1
from ptbutil.files.functions import absolute_path, timestampped_filename
from ptbutil.validation.types import validate_type
from ptbutil.store.quickstore import QuickStore, CollectionProxy



def textdepo_hash(text) -> str:
    """
    Generate a SHA-1 hash for the given text.

    Args:
        text (str): The input text to be hashed.

    Returns:
        str: The hexadecimal digest of the SHA-1 hash.
    """
    return sha1(text.encode()).hexdigest()

def conditional_check(condition, s: str) -> bool:
    if isinstance(condition, str):
        return condition in s
    elif callable(condition):
        res = condition(s)
        if not isinstance (res, bool):
            raise ValueError(f'condition checking callable must return bool. Got {type(res)}')
        return res
    else:
        raise TypeError(f'condition must be str or Callable returning bool.')

class TextDepoIndex(QuickStore):
    """
        A subclass of QuickStore for managing the file index of TextDepo.

        This class provides methods for setting, getting, and checking the presence
        of items in the file index.
    """

    def set(self, k, v) ->CollectionProxy :
        return self['files_index'].update({k: v})

    def get(self,k ) -> Any:
        return self['files_index'].value.get(k)

    def __contains__(self, item) -> bool:
        try:
            return item in self['files_index'].value.keys()
        except KeyError:
            return False

    def __len__(self) -> int:
        return len(self['files_index'].value)


@dataclass
class FileDescriptor:
    hash: str
    len: int
    time: str
    filename: str

    def as_dict(self):
        return self.__dict__


class TextDepo:
    """
        A class for managing text storage and retrieval in a specified directory.

        This class provides methods for writing and reading text files, as well as
        maintaining an index of stored files.
    """

    def __init__(self,
                 dir_path: Union[str, pathlib.Path],
                 file_name: Optional = None,
                 encoding='utf-8') -> None:
        self.dir_path = absolute_path(dir_path)
        if not os.path.isdir(self.dir_path):
            raise FileNotFoundError(f'Could not instantiate TextDepo in {self.dir_path}, '
                                    f'because this directory does not exist.')
        self.file_name = file_name
        self.encoding = encoding
        self.index = TextDepoIndex(os.path.join(self.dir_path, f'{self.file_name}.index'))


    def cook_descriptor(self, text) -> FileDescriptor:
        return FileDescriptor(hash=textdepo_hash(text),
                              len=len(text),
                              time=time.strftime('%Y%m%dT%X', time.localtime()),
                              filename=timestampped_filename(prefix=self.file_name,
                                                             extension='txt',
                                                             timeformat='%Y%m%dT%H%M%S',
                                                             precision=True))


    def write(self, text: str, drop_duplicates=True) -> None:
        validate_type(text, str, error_message='TextDepo can only write type str.')

        descriptor = self.cook_descriptor(text)

        if drop_duplicates and descriptor.hash in self.index:
            return
        else:
            file_name = descriptor.filename
            path = os.path.join(self.dir_path, file_name)
            with open(path, 'w', encoding=self.encoding) as f:
                f.write(text)
            self.index.set(descriptor.hash, descriptor.as_dict()).dump()

    def write_many(self, texts: Iterable, drop_duplicates=True) -> None:
        validate_type(texts, IterableType, error_message='Method write_many accepts Iterable type only.')
        for t in texts:
            self.write(t, drop_duplicates=drop_duplicates)

    def read(self,
             filename: Optional[str] = None,
             condition: Optional[Union[Callable, str]] = None) -> str:
        if not (filename or condition):
            raise ValueError('Expected one of arguments: filename or condition')

        if filename:
            if os.path.isfile(filename):
                if os.path.dirname(filename) == self.dir_path:
                    file_path = filename
                else:
                    raise ValueError(f'file {filename} does not belong to {self}')
            elif os.path.isfile(f := os.path.join(self.dir_path, filename)):
                file_path = f
            else:
                raise FileNotFoundError (f'{filename}')
            with open(file_path, 'r', encoding=self.encoding) as file:
                return file.read()
        else:
            files = os.listdir(self.dir_path)
            files = [f for f in files if f.endswith('txt') and conditional_check(condition, f)]
            if files:
                return self.read(filename=files[0])
            else:
                return None

    def read_many(self, condition: Union[Callable, str]) -> Generator:
        files = os.listdir(self.dir_path)
        files = (f for f in files if f.endswith('txt') and conditional_check(condition, f))
        for filename in files:
            yield self.read(filename=filename)

    def __repr__(self):
        return (f'<TextDepo dir:{self.dir_path}, len={len(self.index)}>')
