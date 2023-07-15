"""
This module delivers a Stats class.
Class Stats is a subclass of Overseer. It's registry differs from Overseer registry, however.
Also the default declaration method is keep, not oversee

use:

class A:
    def __init__(self):
        self.a = 1

        ### instantiation of Stats
        self.stats = Stats(self)

        ### declaration of stats for valid stats check VALID_STATS
        self.stats.keep('count_calls', self.b)
        self.stats.keep('count_returns', self.b)

    def b(self):
        pass

### class A instantiation
a = A()

### lets perform some method calls
for _ in range(3):
    a.b()


### Access to instance stats:
### output is a dict of stats
>>>a.stats.registry

OUTPUT:  {'CountCalls:b': 3, 'CountReturns:b': 3}

### Access to globals stats
### output is a StatsRegistryPrimaryDict
>>> Stats.registry

OUTPUT:  StatsRegistryPrimaryDict(<function classstats.models.stats_instance_registry()>,
                  {'A': defaultdict(dict,
                               {4397438912: {'CountCalls:b': 3,
                                 'CountReturns:b': 3}})})

### StatsRegistryPrimaryDict can be reduced if there is only one instance of a class monitored:
### the output is also cast built-in dict type
>>> Stats.registry.reduce()  # reduces instance subdict if there is only one instance monitored
OUTPUT: {'A': {'CountCalls:b': 3, 'CountReturns:b': 3}}

### StatsRegistryPrimaryDict can be cast to buit-in dict types without reduction
>>> Stats.registry.cast()  # casts to buili-it types
OUTPUT: {'A': {4397438912: {'CountCalls:b': 3, 'CountReturns:b': 3}}}
"""


import time
from ptbutil.meta.overseer import *
from abc import ABC
from types import MethodType
from collections import defaultdict
import datetime


class StatsError(Exception):
    pass


class StatsValue:
    pass


class StatsFloatValue(float, StatsValue):
    def __add__(self, other: int):
        return self.__class__(int(self) + other)


class StatsIntValue(int, StatsValue):
    def __add__(self, other: int):
        return self.__class__(int(self) + other)


def stats_instance_registry():
    """
    the instance registry is a dict of:
    stat_key: stat_value
    where stat_key is a compilation of statname and overseen method separated by a collon
    stat_value is the value of the statistic
    :return:
    """
    return defaultdict(dict)


class StatsRegistryObject(Castable):
    pass


class StatsRegistryDict(defaultdict, StatsRegistryObject):
    pass


class StatsRegistryPrimaryDict(StatsRegistryDict):
    def reduce(self):
        reduced = StatsRegistryPrimaryDict()
        for k, v in self.items():
            if len(v) == 1:
                reduced[k] = v[tuple(v.keys())[0]]
            else:
                reduced[k] = v
        return reduced


class StatsRegistrySecondaryDict(StatsRegistryDict):
    pass


class StatsRegistryTertiaryDict(StatsRegistryDict):
    pass


def secondary_dict_factory():
    """factory for default secondary dict of StatsRegistry"""
    return StatsRegistrySecondaryDict(StatsRegistryTertiaryDict)


def get_stats_registry_primary_dict():
    return StatsRegistryPrimaryDict(secondary_dict_factory)


class StatsRegistry:
    """
    a descriptor registry for Stats class
    data is stored in StatsRegistry._registry
        - the pirmary dict that holds secondary dicts that hold tertiary dicts of stats.
    """

    def __set_name__(self, sts_class, name):
        sts_class._registry = get_stats_registry_primary_dict()

    def __get__(self, sts_instance, sts_class) -> Union[list, dict]:
        if not sts_instance:
            return sts_class._registry
        else:
            return sts_class._registry[sts_instance.owner_instance.__class__.__name__][id(sts_instance.owner_instance)]


class Stats:
    """
    It uses Stat objects to keep stats
    It uses Overseer powers to wrap methods
        see: Stat implementation

    Stats.registry keeps the statistics.
    It is updated by Stat objects injected by Stats.keep method.
    """
    registry = StatsRegistry()

    def __init__(self, owner_instance):

        try:
            if not isinstance(owner_instance.overseer, Overseer):
                raise StatsError(f'Could not instantiate Stats in {owner_instance}') from \
                    RuntimeError(f'Expected Overseer in {owner_instance}')
        except AttributeError:
            owner_instance.overseer = Overseer(owner_instance)
            self.owner_instance = owner_instance
            owner_instance.stats = self  # is this neccesary

    def keep(self, stat, var) -> None:
        """
        :param stat: str | Stat - name of the stat to be used or the stat owner_instance
        :param var: overseen owner_instance object to keep the stats of eg. method or attribute
        :return:
        """

        if stat in VALID_STATS:
            VALID_STATS[stat](self, var)
        elif stat in VALID_STATS.values():
            stat(self, var)
        else:
            raise ValueError(f'{stat} is not a valid stat. For valid stats check classstats.VALID_STATS')


class Stat(ABC):
    """
    abstract base class for stat operation
    Stat objects excercise Stats.owner_instance.overseer.oversee method to wrap methods and keep the statistics.
    :param stats: - Stats instance (Overseer subclass)
    :param var: - instance method (attribute or property not implemented yet) to keep the stats of

    Attributes:
        stats - owner Stats - it has access to owner instance (to keek the stats of)
        overseer - owner Stats owner instance overseer
        var - the owner instance object to keep the stats of


    Implementation
        method overseer must use self.overseer.oversee method to inject handles to keep the stats.
        like:
        self.overseer.oversee(self.var, before_call=self.increment, register=False)

        in the case above method increment is a auxiliary method to change the state of the owner stats registry

    """
    def __init__(self, stats: Stats, var: object):
        self.stats = stats
        self.overseer = self.stats.owner_instance.overseer
        self.var = var
        try:
            self.owner_instance = self.stats.owner_instance
        except AttributeError as e:
            raise AttributeError(f'Stats {self.__class__.__name__} can not be instantiated before Stats.') from e

    @property
    def key(self):
        if isinstance(self.var, MethodType):
            name = self.var.__name__
        else:
            raise  # properties not implemented yet
        return f'{self.__class__.__name__}:{name}'


class MethodStat(Stat):
    """
    base class for all stats dealing with methods
    """
    def __init__(self, stats: Stats, method: MethodType):
        super().__init__(stats, var=method)
        if not isinstance(self.var, MethodType):
            raise TypeError(f'CaountCalls Stat can only count calls of a MethodType. '
                            f'{self.var} is not a MethodType.')
        self.oversee()

    def oversee(self):
        ...


class CountCalls(MethodStat):
    def oversee(self):
        self.overseer.oversee(self.var, before_call=self.increment, register=False)
        self.stats.registry[self.key] = StatsIntValue(0)

    def increment(self):
        self.stats.registry[self.key] += 1


class CountReturns(MethodStat):
    def oversee(self):
        self.overseer.oversee(self.var, after_return=self.increment, register=False)
        self.stats.registry[self.key] = StatsIntValue(0)

    def increment(self):
        self.stats.registry[self.key] += 1


class LastCall(MethodStat):
    def oversee(self):
        self.overseer.oversee(self.var, before_call=self.increment, register=False)
        self.stats.registry[self.key] = None

    def increment(self):
        self.stats.registry[self.key] = datetime.datetime.now()


class LastReturn(LastCall):

    def oversee(self):
        self.overseer.oversee(self.var, after_return=self.increment, register=False)
        self.stats.registry[self.key] = None


class MethodTimeing(MethodStat):
    def oversee(self):
        self.overseer.oversee(self.var, before_call=self.register_start, after_return=self.count_duration,
                              register=False)

    def register_start(self):
        self.start = time.perf_counter()

    def count_duration(self):
        self.stats.registry[self.key] = time.perf_counter() - self.start


class MaxTiming(MethodTimeing):
    def count_duration(self):
        duration = time.perf_counter() - self.start
        if not hasattr(self, 'duration'):
            self.duration = duration
        else:
            if self.duration < duration:
                self.duration = duration
        self.stats.registry[self.key] = duration


class MinTiming(MethodTimeing):
    def count_duration(self):
        duration = time.perf_counter() - self.start
        if not hasattr(self, 'duration'):
            self.duration = duration
        else:
            if self.duration > duration:
                self.duration = duration
        self.stats.registry[self.key] = duration


VALID_STATS = {'count_calls': CountCalls,
               'count_returns': CountReturns,
               'last_call': LastCall,
               'last_return': LastReturn,
               'time': MethodTimeing,
               'max_time': MaxTiming,
               'min_time': MinTiming}
