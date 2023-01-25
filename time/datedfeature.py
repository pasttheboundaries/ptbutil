import datetime
import pandas as pd
from typing import Iterable, Union, NoReturn, Iterator, Optional, Any
from collections.abc import Mapping, Sequence
import re


def now():
    return datetime.datetime.now()


class DatetimeParsingError(Exception):
    pass


class ClosestTimePoints:
    """
    This class provides an iterator of datetime objects closest to reference date

    At instantiation, it accepts:
    - reference : datetime.datetime or pandas.Timestamp
    - others: Iterable[datetime.datetime | pandas.Timestamp],
        any type if iterable object with nested datetime objects
    - look: int - any of -1, 0, 1, looks for proximity of times in others members aranged for:
        -1 = the past,
        0 = absolute time distance
        1 = future.

    when an iterator is recquired it delivers one by the means of __iter__ method.
    Order of delivered dates is always ascending.

    Depending on look:
     parameter only future or past any (based on absolute time distance) dates will be deliveres in the iterator.

    If times_arry contains datetime that is equal to reference it will be included in the iterator

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

    def __init__(self, reference: datetime.datetime,
                 others: Iterable[datetime.datetime],
                 look: Union[str, int] = 0) -> None:
        self.reference_time = self._validate_datetime(reference)
        self.others_array = tuple(self._validate_datetime(date) for date in others)
        self.look = self._translate_look(look)
        self.iter_indexer = 0
        self.iter_dispenser = None

    @staticmethod
    def _validate_datetime(date) -> Union[datetime.datetime, pd.Timestamp, NoReturn]:
        if isinstance(date, pd.Timestamp):
            return date.to_pydatetime()
        elif isinstance(date, DatedFeature):
            return date.datetime
        elif isinstance(date, datetime.datetime):
            return date
        else:
            raise TypeError(f'Invalid type. Expected datetime object, got {date}.')

    @staticmethod
    def _translate_look(look: int) -> Union[int, NoReturn]:
        if look not in (-1, 0, 1):
            raise ValueError('Invalid look parameter. Try: one of: -1, 0, 1.')
        return look

    def arange(self) -> list:
        if self.look < 0:
            array = [date for date in self.others_array if date <= self.reference_time]
        elif self.look > 0:
            array = [date for date in self.others_array if date >= self.reference_time]
        else:
            array = self.others_array

        return sorted(array, key=lambda x: abs(float((self.reference_time - x).total_seconds())), reverse=False)

    @property
    def first(self):
        if iter_dispenser := tuple(self):
            return iter_dispenser[0]
        else:
            return None

    @property
    def last(self):
        if iter_dispenser := tuple(self):
            return iter_dispenser[-1]
        else:
            return None

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

    _checkable_attrs = 'date datetime time timestamp day data dzień czas'.split()

    def __init__(self,
                 feature,
                 hint: Optional[Any] = None,
                 frmt: Optional[str] = None,
                 dayfirst: bool = True,
                 yearfirst: bool = False,
                 values_search: bool = True,
                 ignore_exceptions: bool = False):
        """

        :param feature:
        :param hint: Any
            DatedFeature primarily searches keys and attributes of the feature for likely names like 'date' or 'time'.
            Hint is to direct search towards appropriate attribute (key in a dict).
            - if a string is passed, it must be name of attribute or property to be parsed to datetime,
            or part of the name (case-insensitive) - will be regex matched
            (for example if object has attribute obj.first_date, hint='date' will match.
            - if any other type: equality will be checked agains the feature keys if the feature is type Mapping.
            (for example: if date is in the feature( type Mapping) under the key=11, hint=11 will match.)
        :param frmt: str - along with datetime time formatting rules, expected date format in a string.
            if None, pandas comprehensive string date parser (used here as the last resort of parsing string)
            will use its own formats.
        :param dayfirst: bool - parsing parameter for pandas.to_datetime,
            default True respects is Polish date formatting
        :param yearfirst: bool - parsing parameter for pandas.to_datetime,
            default False respects Polish date formatting
        :param values_search: bool
            If datetime parseable object is not found in attributes or propperties indicated by hint or
            in default attribute names (DatedFeature._checkable_attrs),
            all other attributes and properties will be searched.
            This is default behaviour and might be blocked by setting values_search to False.
        :param ignore_exceptions: bool. If True, in case of failed parsing will return None.
            If False will raise DatetimeParsingError
        """
        self.hint = hint
        self.frmt = frmt
        self.dayfirst = dayfirst
        self.yearfirst = yearfirst
        self.values_search = values_search
        self.ignore = ignore_exceptions
        self.feature = None
        self._datetime = None
        self.date = None
        self._solve(feature)

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
        elif isinstance(dt, DatedFeature):
            return dt.datetime
        elif isinstance(dt, tuple) and all(type(v) == int for v in dt):
            return datetime.datetime(*dt)
        elif isinstance(dt, str):
            return self._parse_string(dt)
        else:
            raise DatetimeParsingError(f'Could not parse date {dt}')

    @staticmethod
    def _re_attr_check(attr, pattern):
        return bool(re.search(pattern, attr, re.IGNORECASE))

    def _attr_in_checkable(self, attr):
        """
        if dictionary_key flag is True:
        additional match for hints that are not type str will be performed
        """
        if self.hint:
            if isinstance(self.hint, str):
                return self._re_attr_check(attr, self.hint)
            else:
                return attr == self.hint
        else:
            for checkable in self._checkable_attrs:
                if self._re_attr_check(attr, checkable):
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

        if self.values_search:
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

        if self.values_search:
            # checking other values if parseable
            other_attrs = [attr for attr in self.feature.__dict__.keys() if attr not in valid_attrs]
            checkable_values = [self.feature.__getattribute__(attr) for attr in other_attrs]
            if result := self._find_parseable_value(checkable_values):
                return result

        raise DatetimeParsingError(f'Could not find valid attribute name or parseable attribute value in the object.')

    def _seek_string(self, text):
        suspected_values = re.findall(r'\b[\d\-./:\s]+\b', text)
        if result := self._find_parseable_value(suspected_values):
            return result
        else:
            raise DatetimeParsingError(f'Could not find date representation in the passed string.')

    def seek_in_sequence(self):
        if all(isinstance(i, int) for i in self.feature):
            return self._parse_value(tuple(self.feature))
        else:
            return self._find_parseable_value(tuple(self.feature))

    def seek_datetime(self):
        if isinstance(self.feature, str):
            return self._seek_string(self.feature)
        # dict case
        elif isinstance(self.feature, Mapping):
            return self._seek_in_dict()
        elif isinstance(self.feature, Sequence):
            return self.seek_in_sequence()
        else:
            return self._seek_object_attributes()

    def _solve(self, obj: Any):
        if isinstance(obj, DatedFeature):
            self.feature = obj.feature
            self.datetime = obj.datetime
        else:
            self.feature = obj
            try:
                self.datetime = self.seek_datetime()
            except DatetimeParsingError as e:
                if self.ignore:
                    return None
                else:
                    raise DatetimeParsingError(f'Could not cast to DatedFeature. ({repr(obj)})') from e

    @property
    def datetime(self):
        return self._datetime

    @datetime.setter
    def datetime(self, dt):
        self._datetime = dt
        self.date = dt.date()

    def __eq__(self, other):
        if not isinstance(other, DatedFeature):
            other = DatedFeature(other)
        return self.datetime == other.datetime

    def __lt__(self, other):
        if not isinstance(other, DatedFeature):
            other = DatedFeature(other)
        return self.datetime < other.datetime

    def __repr__(self):
        return f'<DatedFeature feature: {type(self.feature)}, datetime: {self.datetime}>'


def closest(reference, others, look=0):
    reference = DatedFeature(reference).datetime
    others_dates = [DatedFeature(other).datetime for other in others]
    closest = ClosestTimePoints(reference, others_dates, look=look).first
    for date, other in zip(others_dates, others):
        if date == closest:
            return other


def ordered(*items):
    if len(items) < 2:
        raise ValueError(f'Could not determine time order for less')
    dfs = sorted([DatedFeature(item) for item in items], key=lambda x: x.datetime, reverse=False)
    return tuple(df for df in dfs)

