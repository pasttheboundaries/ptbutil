

from types import MethodType
from functools import wraps
from datetime import datetime
from typing import Callable, Union, Optional, List, Tuple, Iterable, Any


class OverseerError(Exception):
    pass


def dumb(x):
    return x


def index_or_default(ind, li: list, default):
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


def dict_apply_values(d: dict, l: list, default: Any = None) -> dict:
    """
    applies values taken from the given list by item indexes to numeric (integer) values in a dict
    :param d: dict (to ammend)
    :param l: list (values)
    :param default: default value if integer > len(l) - 1
    :return: dict
    """
    new_dict = dict()
    for k, val in d.items():
        if isinstance(val, int):
            new_val = index_or_default(val, l, default)
        elif isinstance(val, dict):
            new_val = dict_apply_values(val, l, default)
        elif isinstance(val, (list, tuple)):
            new_val = [index_or_default(v, l, default) for v in val]
        else:
            new_val = d[k]
        new_dict[k] = new_val
    return new_dict


class Overseer():
    def __init__(self, owner) -> None:
        self.owner = owner
        self._registry = dict()
        self.history = []

    @staticmethod
    def _compose_dump(store_args, store_times, owner, method_name, when, owner_attributes, text, *args,
                      **kwargs) -> dict:
        dump = {'owner_class': owner.__class__.__name__, 'method': method_name, 'when': when}
        if store_times:
            dump.update({'time': datetime.now()})
        if owner_attributes:
            if isinstance(owner_attributes, (tuple, list)):
                owner_attrs = {k: v for k, v in owner.__dict__.items() if k in owner_attributes}
            else:
                owner_attrs = {owner.__dict__}
            dump.update({'owner_attributes': owner_attrs})
        if store_args:
            if isinstance(store_args, (tuple, list)):
                kwargs = {k: v for k, v in kwargs.items() if k in store_args}
                dump.update({'kwargs': kwargs})
            else:
                dump.update({'args': args, 'kwargs': kwargs})
        if text:
            dump.update({'text': text})
        return dump

    @staticmethod
    def _compose_result(result, store_result) -> dict:
        if isinstance(store_result, bool):
            store_result = dumb

        if isinstance(store_result, Callable):
            pass
        else:
            raise TypeError('Overseer.oversee store_result parameter must be bool or a callable.')

        try:
            transformed_result = store_result(result)
        except (TypeError, ValueError):
            transformed_result = 'Error at result transformation.'
        return {'result': transformed_result}

    @staticmethod
    def manage_oversee_hook_calls(call_hook):
        if isinstance(call_hook, Callable):
            call_hook()
        if isinstance(call_hook, (list, tuple, set)):
            for call in call_hook:
                if isinstance(call, Callable):
                    call()

    @property
    def last_event(self):
        if self.history:
            return self.history[-1]
        else:
            return None

    def oversee(self,
                method,
                store_args: Union[bool, tuple, list] = False,
                store_times: bool = True,
                store_result: Union[bool, Callable] = False,
                owner_attributes: Union[bool, tuple, list] = False,
                before_call: Union[bool, Callable, Iterable] = False,
                after_return: Union[bool, Callable, Iterable] = False,
                text: str = None) -> None:
        """

        :param method: method object to be registered
        :param store_args:
            if True: all arguments passed to the method will be stored
            if list or tuple - only indicated key arguments will be stored
            if False (default) - arguments will not be stored
        :param store_times: bool- default is True
        :param store_result: bool- default is False
            if True - method result will be stored
            if Callable, method result will be passed to the callable and result will be stored (eg. str)
        :param owner_attributes:
            if True - all owner atributes will be stored
            if list or tuple - indicated owner attributes will be stored
            default is False
        :param before_call:
            if True: (default) method will be overseen before the method is called
            if callable: the callable will be called before the method is called
        :param after_return:
            if True: method will be overseen after method returns
            if callable: the callable will be called after method returns
            default is False
        :param text: str - to be stored

        If neither before_call nor after_return is True, before_call will be True

        :return: the method return
        """
        method_name = method.__name__
        method_self = method.__self__
        if not any((before_call, after_return)):
            before_call = True

        @wraps(method)
        def wrapper_method(owner, *args, **kwargs):
            nonlocal method_self, method_name, store_args, store_times, store_result, owner_attributes, text
            if before_call:
                when = 'called'
                dump = self._compose_dump(store_args, store_times, owner, method_name, when, owner_attributes, text,
                                          *args, **kwargs)
                self._registry[id(method_self)][method_name].append(len(self.history))
                self.history.append(dump)
                self.manage_oversee_hook_calls(before_call)

            result = method(*args, **kwargs)

            if after_return:
                when = 'returned'
                dump = self._compose_dump(store_args, store_times, owner, method_name, when, owner_attributes, text,
                                          *args, **kwargs)

                if store_result:
                    dump.update(self._compose_result(result, store_result))

                self._registry[id(method_self)][method_name].append(len(self.history))
                self.history.append(dump)
                self.manage_oversee_hook_calls(after_return)

            return result

        new_method = MethodType(wrapper_method, method_self)
        method_self.__setattr__(method_name, new_method)

        if id(method_self) not in self._registry:
            self._registry[id(method_self)] = dict()
        self._registry[id(method_self)][method_name] = []

    @property
    def registry(self):
        return dict_apply_values(self._registry, self.history, False)
