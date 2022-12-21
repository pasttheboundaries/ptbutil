import datetime
import pandas as pd

from typing import Iterable, Union, NoReturn, Iterator, Optional
from ptbutil.errors import ParsingError


class DatetimeParsingError(Exception):
    pass

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
    or follows a hint parameter to search for matching propperty or attribute.

    If 2 attributes or keyed values hold date or time details - the first found is treated as the one.

    If extended_search is True - all other parameters or attributes will be searched,

    If datetime parseable value is not found it rises DatetimeParsingError

    it holds 2 properties:
    - feature (the examined object itself)
    - datetime - extracted and parsed datetime.datetime





    """

    _checkable_attrs = 'date datetime time timestamp day'.split()

    def __init__(self,
                 feature,
                 hint: Optional[str] = None,
                 frmt: Optional[str] = None,
                 dayfirst: bool = True,
                 yearfirst: bool = False,
                 extended_search: bool = False):
        """

        :param feature:
        :param hint: str - name of attribute or property to be parsed or part of it (case sensitive)
        :param frmt: str -  along with satetime time formatting rules
        :param dayfirst: bool - parsing parameter for pandas.to_datetime,
            default True respects is Polish date formatting
        :param yearfirst: bool - parsing parameter for pandas.to_datetime,
            default False respects Polish date formatting
        :param extended_search: bool
            - if datetime parseable object is not found in attributes or propperties indicated by hint or
            in default attribute names (DatedFeature._checkable_attrs),
            all other attributes and properties will be searched.
        """

        self.feature = feature
        self.hint = hint
        self.frmt = frmt
        self.dayfirst = dayfirst
        self.yearfirst = yearfirst
        self.extended_search = extended_search
        self.datetime = self.seek_datetime()

    @staticmethod
    def _from_isoformat(dt):
        try:
            return datetime.datetime.fromisoformat(dt)
        except ValueError:
            raise DatetimeParsingError(f'Could not parse date {dt}')

    def _parse_string(self, dt):
        """
        attempts to use pd.to_datetime and re-passes to _parse_value to return datetime.datetime

        if this fails tries _from_isoformat
        """
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
            raise DatetimeParsingError(f'Could not parse date {dt}')

    def _re_attr_check(self, attr, pattern):
        return bool(re.search(pattern, attr))

    def _attr_in_checkable(self, attr):
        if self.hint:
            checkable_attrs = [self.hint]
        else:
            checkable_attrs = self._checkable_attrs
        for checkable in checkable_attrs:
            if bool(re.search(checkable, attr)):
                return True
        return False


    def _find_parseable_value(self, values: Iterable) -> Union[datetime.datetime, None]:
        for value in values:
            try:
                return self._parse_value(value)
            except DatetimeParsingError:
                pass
        return None

    def _seek_in_dict(self):
        # checking items indicated by hint or _checkable_attrs:
        valid_keys = tuple(key for key in self.feature.keys() if self._attr_in_checkable(key))
        checkable_values = [self.feature[key] for key in valid_keys]
        if result := self._find_parseable_value(checkable_values):
            return result

        if self.extended_search:
            # checking other values if parseable
            other_values = [value for key, value in self.feature.items() if key not in valid_keys]
            if result := self._find_parseable_value(other_values):
                return result

        raise DatetimeParsingError(f'Could not find valid key or parseable value in dict.')

    def _seek_object_attributes(self):

        # checking attributes indicated by hint or _checkable_attrs:
        valid_attrs = tuple(attr for attr in self.feature.__dict__.keys() if self._attr_in_checkable(attr))
        checkable_values = [self.feature.__getattribute__(attr) for attr in valid_attrs]
        if result := self._find_parseable_value(checkable_values):
            return result

        if self.extended_search:
            # checking other values if parseable
            other_attrs = [attr for attr in self.feature.__dict__.keys() if attr not in valid_attrs]
            checkable_values = [self.feature.__getattribute__(attr) for attr in other_attrs]
            if result := self._find_parseable_value(checkable_values):
                return result

        raise DatetimeParsingError(f'Could not find valid attribute name or parseable attribute value in the object.')


    def _seek_string(self, text):
        suspected_values = re.findall(r'\b[\d-./:]+\b', text)
        if result := self._find_parseable_value(suspected_values):
            return result
        else:
            raise DatetimeParsingError(f'Could not find date representation in the passed string.')

    def seek_datetime(self):
        if isinstance(self.feature, str):
            return self._seek_string(self.feature)
        # dict case
        elif isinstance(self.feature, dict):
            return self._seek_in_dict()
        else:
            return self._seek_object_attributes()

    def __repr__(self):
        return f'<DatedFeature> {type(self.feature)}, datetime: {self.datetime}'
