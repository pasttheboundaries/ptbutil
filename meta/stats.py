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
### output is a StatsRegistryDict
>>> Stats.registry

OUTPUT:  StatsRegistryDict(<function classstats.models.stats_instance_registry()>,
                  {'A': defaultdict(dict,
                               {4397438912: {'CountCalls:b': 3,
                                 'CountReturns:b': 3}})})

### StatsRegistryDict can be reduced if there is only one instance of a class monitored:
### the output is also cast built-in dict type
>>> Stats.registry.reduce()  # reduces instance subdict if there is only one instance monitored
OUTPUT: {'A': {'CountCalls:b': 3, 'CountReturns:b': 3}}

### StatsRegistryDict can be cast to buit-in dict types without reduction
>>> Stats.registry.cast()  # casts to buili-it types
OUTPUT: {'A': {4397438912: {'CountCalls:b': 3, 'CountReturns:b': 3}}}

"""


from ptbutil.meta.overseer import Overseer, OverseerRegistry, OverseerRegistryDict
from abc import ABC
from types import MethodType
from collections import defaultdict
from dataclasses import dataclass
from typing import Any
import datetime


def stats_instance_registry():
    """
    the instance registry is a dict of:
    stat_key: stat_value
    where stat_key is a compilation of statname and overseen method separated by a collon
    stat_valu is the value of the statistic
    :return:
    """
    return defaultdict(dict)


# @dataclass
# class StatsItem:
#     name: str
#     value: Any


class StatsRegistryDict(OverseerRegistryDict):
    """
    this inherits form OverseerRegistryDict, that implements methods reduce and cast
    """
    pass


class StatsRegistry(OverseerRegistry):
    """
    This inherits from OverseerRegistry that is used as a Overseer (here: Stats) class registry descriptor.
    The difference is it implements a different stats instance registry which is a dict
    """

    def __init__(self):
        super().__init__()
        self.registry = StatsRegistryDict(stats_instance_registry)


class Stats(Overseer):
    """
    Overseer subclass
    It uses Stat objects to keep stats
    It uses Overseer powers to wrap methods
    Stats.oversee method is to be used within a Stat object
    """
    registry = StatsRegistry()

    def __init__(self, owner_instance):
        super().__init__(owner_instance)

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
            raise ValueError(f'{var} is not a valid stat. For valid stats check classstats.VALID_STATS')


class Stat(ABC):
    """
    abstract base class for stat operation
    Stat objects excercise Stats.oversee method (inherited form overseer) to wrap methods and keep the statistics.
    :param stats: - Stats instance (Overseer subclass)
    :param var: - instance method (attribute or property not implemented yet) to keep the stats of
    """
    def __init__(self, stats: Overseer, var: object):
        self.stats = stats
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
        self.stats.oversee(self.var, before_call=self.increment, register=False)
        self.stats.registry[self.key] = 0

    def increment(self):
        self.stats.registry[self.key] += 1


class CountReturns(MethodStat):
    def oversee(self):
        self.stats.oversee(self.var, after_return=self.increment, register=False)
        self.stats.registry[self.key] = 0

    def increment(self):
        self.stats.registry[self.key] += 1


class LastCall(MethodStat):
    def oversee(self):
        self.stats.oversee(self.var, before_call=self.increment, register=False)
        self.stats.registry[self.key] = 0

    def increment(self):
        self.stats.registry[self.key] = datetime.datetime.now()


class LastReturn(LastCall):
    def oversee(self):
        self.stats.oversee(self.var, after_return=self.increment, register=False)
        self.stats.registry[self.key] = 0


VALID_STATS = {'count_calls': CountCalls,
               'count_returns': CountReturns,
               'last_call': LastCall,
               'last_return': LastReturn}
