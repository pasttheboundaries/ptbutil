"""
DomainFimeNamseRotator is a class manipulating database filenames by the domainname

"""

import os
import re
from typing import Optional, Union
import pathlib
from .errors import Unable


class FileNamesRotator:
    """
    Governs the domain filenames
    current: returns current filename
    next: retruns next afeter last filename
    apply_index: renames unindexed data to 0
    """
    def __init__(self,
                 directory,
                 domain,
                 extension,
                 digit_separator='_'):
        self.domain = domain
        self.directory = str(pathlib.Path(directory).absolute())
        self.extension = extension
        self.dig_sep = digit_separator
        self.available_files = self.existing_files  # alias

    def existing_files(self, path: bool = False) -> list:
        available_files = os.listdir(self.directory)
        re_ = re.compile(fr'{self.domain}({self.dig_sep}\d+)?[.]{self.extension}')
        available_files = [f for f in available_files if re_.fullmatch(f)]
        if path:
            available_files = [os.path.join(self.directory, f) for f in available_files]
        # print('available existing_files', available_files)
        return available_files

    def extraxt_index(self, filename: str) -> Union[int, None]:
        pattern = fr'{self.domain}{self.dig_sep}?(\d+)[.]{self.extension}'
        try:
            digit = re.search(pattern, filename).groups()[0]
            if not digit:
                return None
            else:
                return int(digit)
        except AttributeError:
            return None

    def current_index(self) -> Union[None, int]:
        numbers = [self.extraxt_index(file) for file in self.existing_files(path=False)]
        numbers = [n for n in numbers if n is not None]
        if not numbers:
            return None
        else:
            return max(numbers)

    def next_index(self) -> int:
        last_ind = self.current_index()
        if not last_ind:
            return 1
        else:
            return last_ind + 1

    def construct_file_name(self, number: Optional[int] = None, path=False) -> str:
        if number is None:
            number = ''
        else:
            number = f'{self.dig_sep}{number}'
        fn = f'{self.domain}{number}.{self.extension}'
        if path:
            return os.path.join(self.directory, fn)
        else:
            return fn

    def _create_next_file(self) -> str:
        next_file = self.construct_file_name(self.current_index() + 1)
        return next_file

    def current(self, path=True) -> str:
        """
        :param path:
        :return:
        """
        return self.construct_file_name(None, path=path)

    def apply_index(self) -> None:
        """
        renames unindexed data to index 0
        """
        unindexed = self.construct_file_name(path=True)
        indexed = self.construct_file_name(0, path=True)
        if os.path.exists(indexed):
            raise FileExistsError(f'Can not rename to {indexed}, because this file already exists.')
        try:
            os.rename(unindexed, indexed)
        except FileNotFoundError:
            raise FileNotFoundError(f'Unindexed file: {unindexed} not found')

    def increase_index(self, filename, path=False):
        current_ind = self.extraxt_index(filename)
        return self.construct_file_name(current_ind + 1, path=path)

    def decrease_index(self, filename, path=False):
        current_ind = self.extraxt_index(filename)
        return self.construct_file_name(current_ind - 1, path=path)

    def rotate_up(self) -> None:
        """
        rotates indexed files up
        :return:
        """
        current_files = ((self.extraxt_index(f), f) for f in self.existing_files(path=True))
        current_files = [cf for cf in current_files if cf[0] is not None]
        current_files = sorted(current_files, key=lambda x: x[0], reverse=True)
        for ind, fname in current_files:
            upped = self.increase_index(fname, path=True)
            os.rename(fname, upped)

    def rotate_down(self) -> None:
        """
        rotates indexed files down
        :return:
        """
        current_files = ((self.extraxt_index(f), f) for f in self.existing_files(path=True))
        current_files = [cf for cf in current_files if cf[0] is not None]
        current_files = sorted(current_files, key=lambda x: x[0], reverse=False)
        if not current_files:
            raise Unable
        if current_files[0][0] < 1:  # can not rotate down if lowest index is 0
            raise Unable
        for ind, fname in current_files:
            downed = self.decrease_index(fname, path=True)
            os.rename(fname, downed)

    def rotate(self):
        while True:
            try:
                self.rotate_down()
            except Unable: # lowest index= 0
                break
        self.rotate_up()  # lowesrt index = 1

        try:
            self.apply_index()  # current data indexed with 0
        except OSError as e:
            raise Unable('Could not apply index to unindexed file. '
                         'This may happen if there is no file to rotate name.') from e
        else:
            self.rotate_up()  # lowesrt index = 1



