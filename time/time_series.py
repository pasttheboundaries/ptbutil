import datetime
import pandas as pd

from typing import Iterable, Union, NoReturn, Iterator, Optional
from ptbutil.errors import ParsingError


class ClosestTimePoints:
    """
    This class provides an iterator of datetime objects closest to time_zero date

    At instantiation, it accepts:
    - time_zero : datetime.datetime or pandas.Timestamp
    - times_array: Iterable[datetime.datetime | pandas.Timestamp],
        any type if iterable object with nested datetime objects
    - look: str | int - any of -1, 0, 1, 'forward', 'future', 'ahead', 'back', 'past', 'aroud', 'round'

    when an iterator is recquired it delivers one by the means of __iter__ method.
    Order of delivered dates is always ascending.

    Depending on look:
     parameter only future or past any (based on absolute time distance) dates will be deliveres in the iterator.

    If times_arry contains datetime that is equal to time_zero it will be included in the iterator

    Use:

    dates = [Timestamp('2018-08-31 15:31:00'), Timestamp('2018-04-26 23:08:00'), Timestamp('2018-04-17 17:41:00')]
    zero_time = Timestamp('2018-04-26 23:08:00')
    CTParound = ClosestTimePoint(zero_time, dates, look=0)
    for ctp in CTParound:
        print(ctp)

    Output:
    2018-04-26 23:08:00
    2018-04-17 17:41:00
    2018-08-31 15:31:00

    CTPpast = ClosestTimePoint(zero_time, dates, look=-1)
    for ctp in CTPpast:
        print(ctp)

    Output:
    2018-04-26 23:08:00
    2018-04-17 17:41:00
    """

    def __init__(self, time_zero: datetime.datetime,
                 times_array: Iterable[datetime.datetime],
                 look='around') -> None:
        self.time_zero = self._validate_datetime(time_zero)
        self.times_array = tuple(self._validate_datetime(date) for date in times_array)
        self.look = self._translate_look(look)
        self.iter_indexer = 0
        self.iter_dispenser = None

    @staticmethod
    def _validate_datetime(date) -> Union[datetime.datetime, pd.Timestamp, NoReturn]:
        if isinstance(date, pd.Timestamp):
            return date.to_pydatetime()
        elif isinstance(date, datetime.datetime):
            return date
        else:
            raise TypeError(f'Invalid type. Expected datetime object, got {date}.')

    @staticmethod
    def _translate_look(look) -> Union[int, NoReturn]:
        ld = {0: ('around', 'round', 'r'),
              -1: ('back', 'behind', 'b', 'past', 'p'),
              1: ('forward', 'future', 'ahead', 'a', 'f')}
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

        return sorted(array, key=lambda x: abs(float((self.time_zero - x).total_seconds())), reverse=False)

    def __iter__(self) -> Iterator:
        self.iter_indexer = 0
        self.iter_dispenser = self.iter_dispenser or self.arange()
        return self

    def __next__(self) -> Union[datetime.datetime, pd.Timestamp]:
        try:
            return self.iter_dispenser[self.iter_indexer]
        except IndexError:
            raise StopIteration
        finally:
            self.iter_indexer += 1

    def __getitem__(self, item):
        self.iter_dispenser = self.iter_dispenser or self.arange()
        return self.iter_dispenser[item]


class DatedFeature:
    """
    This class is a wrapper for objects that potentially contain information about date (and time)
    It seeks most likely atributes for values that could be parsed to datetime.datetime

    it holds 2 properties:
    - feature (the examined object itself)
    - datetime - extracted and parsed datetime.datetime

    If 2 attributes or keyed values hold date or time details - the first found is treated as the one.


    """

    _checkable_attrs = 'date datetime time timestamp t day'.split()

    def __init__(self,
                 feature,
                 frmt: Optional[str] = None,
                 dayfirst: bool = True,
                 yearfirst: bool = False):
        """

        :param feature:
        :param frmt: str -  along with satetime time formatting rules
        :param dayfirst: bool - parsing parameter for pandas.to_datetime,
            default True respects is Polish date formatting
        :param yearfirst: bool - parsing parameter for pandas.to_datetime,
            default False respects Polish date formatting
        """

        self.feature = feature
        self.frmt = frmt
        self.dayfirst = dayfirst
        self.yearfirst = yearfirst
        self.datetime = self.seek_datetime()

    @staticmethod
    def _from_isoformat(dt):
        try:
            return datetime.datetime.fromisoformat(dt)
        except ValueError:
            raise ParsingError(f'Could not parse date {dt}')

    def _parse_string(self, dt):
        try:
            return self._parse_value(
                pd.to_datetime(
                    dt,
                    format=self.frmt,
                    dayfirst=self.dayfirst,
                    yearfirst=self.yearfirst
                )
            )
        except ValueError:
            return self._from_isoformat(dt)

    def _parse_value(self, dt):
        if isinstance(dt, pd.Timestamp):
            return dt.to_pydatetime()
        elif isinstance(dt, datetime.datetime):
            return dt
        elif isinstance(dt, tuple) and all(type(v) == int for v in dt):
            return datetime.datetime(*dt)
        elif isinstance(dt, str):
            return self._parse_string(dt)
        else:
            raise ParsingError(f'Could not parse date {dt}')

    def _seek_in_dict(self):
        valid_attrs = tuple(key for key in self.feature.keys() if key in self._checkable_attrs)

        if not any(valid_attrs):
            raise KeyError(f'Could not find suitabale keys in a dict')

        for key in valid_attrs:
            try:
                return self._parse_value(self.feature[key])
            except ParsingError as e:
                raise ParsingError(f'Found key {key} but could not parse it') from e

    def _seek_object_attributes(self):
        valid_attrs = tuple(attr for attr in self._checkable_attrs if hasattr(self.feature, attr))
        if not any(valid_attrs):
            raise AttributeError(f'Could not find suitabale attribute')

        for attr in valid_attrs:
            try:
                return self._parse_value(self.feature.__getattribute__(attr))
            except ParsingError:
                pass
        raise ParsingError(f'Found attributes {valid_attrs} but could not parse any.')

    def seek_datetime(self):
        if isinstance(self.feature, str):
            return self._parse_string(self.feature)
        # dict case
        elif isinstance(self.feature, dict):
            return self._seek_in_dict()
        else:
            return self._seek_object_attributes()
