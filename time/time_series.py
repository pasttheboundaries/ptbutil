import datetime
import pandas as pd

from typing import Iterable



class ClosestTimePoint:
    def __init__(self, time_zero: datetime.datetime, times_array: Iterable[datetime.datetime], look='around'):
        self.time_zero = self._validate_datetime(time_zero)
        self.times_array = tuple(self._validate_datetime(date) for date in times_array)
        self.look = self._translate_look(look)
        self.iter_indexer = 0
        self.iter_dispenser = None

    @staticmethod
    def _validate_datetime(date):
        if not isinstance(date, (datetime.datetime, pd.Timestamp)):
            raise TypeError('Invalid type. Expected datetime object.')
        return date

    @staticmethod
    def _translate_look(look):
        ld = {0: ('around', 'round', 'r'),
              -1: ('back', 'behind', 'b', 'past', 'p'),
              1: ('forward', 'ahead', 'a', 'f')}
        for k, v in ld.items():
            if look in v or look == k:
                return k
        raise ValueError('Invalid look parameter. Try: back, around or forward; (or: b, r, f); (or: -1, 0, 1)')

    def _select_future(self) -> list:
        zero_delta = datetime.timedelta(seconds=0)
        return [date for date in self.times_array if date - self.time_zero >= zero_delta]

    def _select_past(self) -> list:
        zero_delta = datetime.timedelta(seconds=0)
        return [date for date in self.times_array if date - self.time_zero <= zero_delta]

    def arange(self) -> list:
        if self.look < 0:
            array = self._select_past()
        elif self.look > 0:
            array = self._select_future()
        else:
            array = self.times_array

        return sorted(array, key=lambda x: abs(int((self.time_zero - x).delta)), reverse=False)

    def __iter__(self):
        self.iter_indexer = 0
        self.iter_dispenser = self.arange()
        return self

    def __next__(self):
        try:
            return self.iter_dispenser[self.iter_indexer]
        except IndexError:
            raise StopIteration
        finally:
            self.iter_indexer += 1