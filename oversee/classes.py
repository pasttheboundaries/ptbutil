
from types import MethodType
from functools import wraps
from datetime import datetime
from typing import Callable, Union, Optional, List, Tuple, Iterable, Any
from collections import UserList, UserDict
from .exceptions import OverseerError


class InstanceOverseerHistory(UserList):

    def append(self, activity_dump: dict) -> None:
        # activity_dump is a dict
        # good place to implement logging
        return super().append(activity_dump)


class OverseerRegistry(UserDict):
    def __get__(self, instance, owner):
        if not instance and type(owner) == type:
            return self
        if not id(instance) in self:
            self[id(instance)] = InstanceOverseerHistory()
        return self[id(instance)]


class Overseer:

    """
    Overseer is ment to me instantiated as an attribute of an instance
    Overseer.oversee method is meant to wrap the object methods at runtime.
    For compile time decorators check oversee.decorators.
    """
    registry = OverseerRegistry()

    def __init__(self, path=None, mode='instance') -> None:
        self.path = path  # TODO
        self.mode = mode  # instance or class TODO


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
            pass
        elif callable(store_result):
            try:
                result = store_result(result)
            except (TypeError, ValueError):
                result = 'Error at result transformation.'
        else:
            raise OverseerError from TypeError('Overseer.oversee store_result parameter must be bool or a callable.')
        return result

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
            if True - all owner instance atributes will be stored (advised against)
            if list or tuple - indicated owner instance attributes will be stored
            default is False
        :param before_call:
            if True: (default) method will be overseen before the method is called
            if callable: the callable will be called before the method is called and the method will be overseen
        :param after_return:
            if True: method will be overseen after method returns
            if callable: the callable will be called after method returns and the method will be overseen
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
        def wrapper_method(owner_self, *args, **kwargs):
            nonlocal method_self, method_name, store_args, store_times, store_result, owner_attributes, text
            if before_call:
                when = 'called'
                dump = self._compose_dump(store_args, store_times, owner_self,
                                          method_name, when, owner_attributes, text,
                                          *args, **kwargs)
                self.registry.append(dump)
                self.manage_oversee_hook_calls(before_call)

            result = method(*args, **kwargs)

            if after_return:
                when = 'returned'
                dump = self._compose_dump(store_args, store_times, owner_self,
                                          method_name, when, owner_attributes, text,
                                          *args, **kwargs)

                if store_result:
                    dump.update({'result': self._compose_result(result, store_result)})

                self.registry.append(dump)
                self.manage_oversee_hook_calls(after_return)

            return result

        new_method = MethodType(wrapper_method, method_self)
        method_self.__setattr__(method_name, new_method)

    @property
    def history(self):
        return self.registry


class DescriptorOverseer:
    """
    Adds Overseer descriptor
    """

    def __get__(self, instance, owner):
        if not hasattr(instance, '_overseer'):
            instance._overseer = Overseer()
        return instance._overseer
