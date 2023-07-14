"""
Overseer


"""

from types import MethodType
from functools import wraps
from datetime import datetime
from typing import Callable, Union, Iterable, Any
from collections import defaultdict
from dataclasses import dataclass
from functools import partial
from ptbutil.errors import DecorationError

class OverseerError(Exception):
    pass


def dumb(x):
    return x


def _index_or_default(ind, li: list, default):
    if not isinstance(ind, int):
        return ind
    try:
        new_val = li[ind]
    except IndexError as ie:
        if default is False:
            raise OverseerError('Could not establish indexing while compiling registry.') from ie
        if default is None:
            new_val = ind
        else:
            new_val = default
    return new_val


def _dict_apply_values(d: dict, l: list, default: Any = None) -> dict:
    """
    ta implementacja jest bez sensu
    overseer.registry przehowuje indeksy wpisów do history po to by móc zrekonstuować overseer.registry
    zastępując indeksy wpisami z historii
    To jest bardziej niż zbyteczne
    Przerobiłem to w osobnym pakiecie oversee

    helper function for Overseer register
    applies values taken from the given list by item indexes to numeric (integer) values in a dict

    eg:
    >>> d = {'A': 1, 'B': 2, 'C': 2, 'D': 4}
    >>> l = ['a', 'b', 'c', 'd']
    >>> _dict_apply_values(d, l)
    {'A': 'b', 'B': 'c', 'C': 'c', 'D': 4}

    :param d: dict (to ammend)
    :param l: list (values)
    :param default: default value if integer > len(l) - 1
    :return: dict
    """
    new_dict = dict()

    for k, val in d.items():
        if isinstance(val, int):
            new_val = _index_or_default(val, l, default)
        elif isinstance(val, dict):
            new_val = _dict_apply_values(val, l, default)
        elif isinstance(val, (list, tuple)):
            new_val = [_index_or_default(v, l, default) for v in val]
        else:
            new_val = d[k]
        new_dict[k] = new_val
    return new_dict


class ReducedOverseerRegistry(dict):
    pass


class OverseerRegistryDict(defaultdict):
    def reduce(self):
        reduced = ReducedOverseerRegistry()
        for k, v in self.items():
            if len(v) == 1:
                vkey = tuple(v.keys())[0]
                reduced[k] = v[vkey]
            else:
                reduced[k] = dict[v]
        return reduced

    def cast(self):
        return {k: dict(v) for k, v in self.items()}


def OverseerInstanceRegistry():
    return defaultdict(list)


class OverseerRegistry:
    def __init__(self):
        self.registry = OverseerRegistryDict(OverseerInstanceRegistry)


    # this will be not necessary as __get__ can direct straight to owner instance reristy lists
    # def __getitem__(self, indices):
    #     if not (isinstance(indices, tuple) and len(indices) == 2):
    #         raise ValueError(f'two indices must be given')
    #     a, b = indices
    #     return self.registry[a][b]

    # this will be not necessary as __get__ can direct straight to owner instance reristy lists
    # def __setitem__(self, indices, val):
    #     if not (isinstance(indices, tuple) and len(indices) == 2):
    #         raise ValueError(f'two indices must be given')
    #     a, b = indices
    #     self.registry[a][b].append(val)

    def __get__(self, ovs_instance, ovs_class) -> Union[list, dict]:
        if not ovs_instance:
            return self.registry
        else:
            return self.registry[ovs_instance.owner_instance.__class__.__name__][id(ovs_instance.owner_instance)]



@dataclass
class OverseerHistoryItem:
    owner_class: str = None
    owner_instance_id: int = None
    method: str = None
    when: str = None
    time: int = None
    owner_attributes: datetime = None
    args: Any = None
    kwargs: dict = None
    text: str = None
    result: Any = None


class OverseerHistory(list):
    pass


class Overseer:
    """
    Overseer is ment to me instantiated as an attribute of an instance
    method oversee is meant to decorate object methods at runtime
    """
    registry = OverseerRegistry()
    history = OverseerHistory()

    def __init__(self, owner_instance) -> None:
        self.owner_instance = owner_instance

    @staticmethod
    def _compose_dump(store_args, store_times, owner_instance, method_name, when, owner_attributes, text, args,
                      kwargs, result) -> OverseerHistoryItem:
        dump = OverseerHistoryItem()
        dump.owner_class = owner_instance.__class__.__name__
        dump.owner_instance_id = id(owner_instance)
        dump.method = method_name
        dump.when = when
        if store_times:
            dump.time = datetime.now()
        if owner_attributes:
            if isinstance(owner_attributes, (tuple, list)):
                owner_attrs = {k: v for k, v in owner_instance.__dict__.items() if k in owner_attributes}
            else:
                owner_attrs = {owner_instance.__dict__}
            dump.owner_attributes = owner_attrs
        if store_args:
            if isinstance(store_args, (tuple, list)):
                kwargs = {k: v for k, v in kwargs.items() if k in store_args}
                dump.kwargs = kwargs
            else:
                dump.args = args
                dump.kwargs = kwargs
        if text:
            dump.text = text
        if result:
            dump.result = result
        return dump

    @staticmethod
    def _compose_result(result, store_result) -> Any:
        if isinstance(store_result, bool):
            transformed_result = result
        elif isinstance(store_result, Callable):
            try:
                transformed_result = store_result(result)
            except (TypeError, ValueError):
                transformed_result = 'Error at result transformation.'
        else:
            raise TypeError('Overseer.oversee store_result parameter must be bool or a callable.')

        return transformed_result

    @staticmethod
    def _manage_oversee_hook_calls(call_hook):
        if isinstance(call_hook, Callable):
            call_hook()
        if isinstance(call_hook, (list, tuple, set)):
            for call in call_hook:
                if isinstance(call, Callable):
                    call()

    @property
    def last_event(self):
        try:
            return self.history[-1]
        except IndexError:
            return None

    def oversee(self,
                method,
                store_args: Union[bool, tuple, list] = False,
                store_times: bool = True,
                store_result: Union[bool, Callable] = False,
                owner_attributes: Union[bool, tuple, list] = False,
                before_call: Union[bool, Callable, Iterable] = False,
                after_return: Union[bool, Callable, Iterable] = False,
                text: str = None,
                register=True) -> None:
        """

        Registers overseen method
        A method activity is stored in Overseer.history if it is registered.

        :param method: types.MethodType - method object to be registered
        :param store_args:
            if True: all arguments passed to the method will be stored
            if list or tuple - only indicated key arguments will be stored
            if False (default) - arguments will not be stored
        :param store_times: bool- default is True
        :param store_result: bool- default is False
            if True - method result will be stored
            if Callable, method result will be passed to the callable and result will be stored (eg. str)
        :param owner_attributes:
            if True - all owner_instance atributes will be stored
            if list or tuple - indicated owner_instance attributes will be stored
            default is False
        :param before_call:
            if True: (default) method will be overseen before the method is called
            if callable: the callable will be called before the method is called and the method will be overseen
        :param after_return:
            if True: method will be overseen after method returns
            if callable: the callable will be called after method returns and the method will be overseen
            default is False
        :param text: str - to be stored
        :param register: bool - Sometimes Overseer might be used for other purposes (eg. method hooks)
            where keeping registry is not needed. In such a case register should be set to False.

        If neither before_call nor after_return is True, before_call will be True

        :return: the method return
        """
        method_name = method.__name__
        method_self = method.__self__
        if not any((before_call, after_return)):
            after_return = True

        @wraps(method)
        def wrapper_method(owner_instance, *args, **kwargs):
            nonlocal method_self, method_name, store_args, store_times, store_result, owner_attributes, text
            if before_call:
                if register:
                    when = 'called'
                    dump = self._compose_dump(store_args, store_times, owner_instance, method_name, when, owner_attributes, text,
                                              args, kwargs, None)
                    self.registry.append(len(self.history))
                    self.history.append(dump)
                self._manage_oversee_hook_calls(before_call)

            result = method(*args, **kwargs)

            if after_return:
                if register:
                    when = 'returned'
                    if store_result:
                        dump_result = self._compose_result(result, store_result)
                    else:
                        dump_result = None
                    dump = self._compose_dump(store_args, store_times, owner_instance, method_name, when, owner_attributes, text,
                                              args, kwargs, dump_result)

                    self.registry.append(len(self.history))
                    self.history.append(dump)
                self._manage_oversee_hook_calls(after_return)

            return result

        new_method = MethodType(wrapper_method, method_self)
        method_self.__setattr__(method_name, new_method)


class DescriptorOverseer:
    """
    Overseer descriptor.
    Stores instance Overseer in _overseer attribute
    """

    def __get__(self, instance, owner):
        if not hasattr(instance, '_overseer'):
            instance._overseer = Overseer()
        return instance._overseer


def _decorate_class(cls, *args, **kwargs):

    old_init = cls.__init__

    def __init__(_self, *instance_args, **instance_kwargs):
        old_init(_self, *instance_args, **instance_kwargs)

        _self.overseer = Overseer()

        for arg in args:
            if not isinstance(arg, str):
                raise DecorationError from TypeError(
                    'oversee decorator arguments must be type str: names for overseen methods')
            cls.overseer.oversee(_self.__getattribute__(arg))

        for method, oversee_kwargs in kwargs.items():
            if not isinstance(method, str):
                raise DecorationError from TypeError(
                    'oversee decorator key_word_arguments keys must be type str: names for overseen methods')
            if not hasattr(_self, method):
                raise ValueError(f'oversee decorator key_word_arguments keys must be names for overseen methods.'
                                 f' method {method} has not been found in the instnce of {cls}')
            if not isinstance(oversee_kwargs, dict):
                raise DecorationError from TypeError(
                    'oversee decorator key_word_arguments values must be type dict,'
                    'and must contain arguments for Overseer.oversee method.'
                    'Check Overseer.oversee.__doc__')
            _self.overseer.oversee(method=_self.__getattribute__(method), **oversee_kwargs)

    cls.__init__ = __init__
    return cls


def oversee(*args, **kwargs):
    """
    this is a class decorator
    it can be used:
     1) on its own - this wrapps the decorated class so it gets the overseer - but no activity will be recorded untill
     instance.overseer.oversee(instance.method) is called at the runtime

     example:
     @oversee
     class MyClass:
        pass

     2) with method names - to oversee methods with default setup
     example:
     @oversee('a', 'c')
     class MyClass:
        def a():
        def b():
        def c():

     3) with a dict of a structure: {method_name: {oversee_kwargs}, ...}
        where oversee_kwargs arge arguments for Overseer.oversee method
     example:
     @oversee({'a':{'before_call':True}, 'c':{'after_return':True, 'store_result':True})
     class MyClass:
        def a(): # will be overseen before the call
        def b():
        def c(): # will be overseen after return, and the result will be stored

    :param args:
    :param kwargs:
    :return: decorated class
    """
    if not kwargs and len(args) == 1 and isinstance(args[0], type):
        return _decorate_class(args[0])
    else:
        return partial(_decorate_class, *args[1:], **kwargs)
