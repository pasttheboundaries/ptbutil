"""
Overseer


"""

from types import MethodType
from functools import wraps, partial
from itertools import chain
from datetime import datetime
from typing import Callable, Union, Iterable, Any
from collections import defaultdict
from dataclasses import dataclass
from ptbutil.errors import DecorationError


class OverseerError(Exception):
    pass


def cast_overseer_registry_object(obj):
    if isinstance(obj, dict):
        return {k: cast_overseer_registry_object(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [cast_overseer_registry_object(v) for v in obj]
    elif isinstance(obj, int):
        return int(obj)
    elif isinstance(obj, float):
        return float(obj)
    elif isinstance(obj, OverseerHistoryItem):
        return vars(obj)
    else:
        return obj


class Castable:
    def cast(self):
        return cast_overseer_registry_object(self)

class Fillable:
    def fill(self):
        return apply_overseer_history_items(self)


class OverseerRegistryObject(Castable, Fillable):
    pass


class OverseerHistory(list, OverseerRegistryObject):
    pass


class OverseerHistoryIndex(int, OverseerRegistryObject):
    pass


@dataclass
class OverseerHistoryItem(OverseerRegistryObject):
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


def apply_overseer_history_items(obj: OverseerRegistryObject) -> Union[OverseerRegistryObject, OverseerHistory]:
    """
    """
    if isinstance(obj, OverseerRegistryDict):
        new = obj.__class__()
        for k, v in obj.items():
            new[k] = apply_overseer_history_items(v)
        return new
    elif isinstance(obj, OverseerRegistryIndicesList):
        return OverseerHistory(apply_overseer_history_items(i) for i in obj)
    elif isinstance(obj, OverseerHistoryIndex):
        return Overseer.history[obj]
    else:
        raise OverseerError from RuntimeError(f'Could not perform register fill with {obj}')


class ReducedOverseerRegistry(dict):
    """default type for reduced dict"""
    pass


class OverseerRegistryDict(defaultdict, OverseerRegistryObject):
    def __repr__(self):
        return f'{self.__class__.__name__}: {self.cast()}'


class OverseerClassRegistry(OverseerRegistryDict):  # former OverseerClassRegistry
    """
    OverseerClassRegistry is the main dict of OverseerRegistry:
    the keys are overseen instance.__class__.__name__
        the values are dicts where keys are id(instance) (type int)
    it implements 3 methods:
    fill: uses the stored indices to build the copy of self filled with values acquired from Overseer.history
        The return object is also OverseerClassRegistry so further reduce or cast methods can be exercised
        However the returned object is a copy of the orifinal one.
    reduce: returns a ReducedOverseerRegistry:
        the secondary dict values are moved and ascribed to the primary dict (__class__.__name__)
    cast: casts the default types to built-in types (dict and list)
    """

    def reduce(self):
        reduced = ReducedOverseerRegistry()
        for k, v in self.items():
            reduced[k] = OverseerHistory(chain(*list(v.values())))
        return reduced


class OverseerRegistrySecondaryDict(OverseerRegistryDict):
    """
    OverseerClassRegistry is the main dict of OverseerRegistry:
    the keys are overseen instance.__class__.__name__
        the values are dicts where keys are id(instance) (type int)
    it implements 3 methods:
    fill: uses the stored indices to build the copy of self filled with values acquired from Overseer.history
        The return object is also OverseerClassRegistry so further reduce or cast methods can be exercised
        However the returned object is a copy of the orifinal one.
    reduce: returns a ReducedOverseerRegistry: in case only one instance of a class is overseen,
        the secondary dict values are moved and ascribed to the primary dict (__class__.__name__)
    cast: casts the default types to built-in types (dict and list)
    """
    pass


class OverseerRegistryIndicesList(list, OverseerRegistryObject):
    pass


def secondary_dict_factory():
    """factory for defaulr secondary dict of OverseerRegistry"""
    return OverseerRegistrySecondaryDict(OverseerRegistryIndicesList)


def get_overseer_registry_primary_dict():
    return OverseerClassRegistry(secondary_dict_factory)


class OverseerRegistry:
    """
    a descriptor registry for Overseer class
    data is stored in OverseerRegistry.registry - the pirmary dict that holds secondary dicts that hold lists of indices
        the indices are to identify history items.
        As the Overseer history stores the actual records of the Overseer.
    """

    def __set_name__(self, ovs_class, name):
        ovs_class._registry = get_overseer_registry_primary_dict()

    def __get__(self, ovs_instance, ovs_class) -> Union[list, dict]:
        if not ovs_instance:
            return ovs_class._registry
        else:
            return ovs_class._registry[ovs_instance.owner_instance.__class__.__name__][id(ovs_instance.owner_instance)]

class OverseerHistoryDescriptor:

    def __get__(self, ovs_instance, ovs_class) -> Union[list, dict]:
        if not hasattr(ovs_class, '_history'):
            ovs_class._history = OverseerHistory()
        if not ovs_instance:
            return ovs_class._history
        else:
            return [ovs_class._history[i] for i in ovs_instance.registry]


class Overseer:
    """
    Overseer is ment to me instantiated as an attribute of an instance
    method oversee is meant to decorate object methods at runtime

    use:

class A:
    def __init__(self):
        self.a = 1

        ### instantiation of Overseer
        self.overseer = Overseer(self)

        ### declaration of overseeing
        self.overseer.oversee(self.b, store_args=True, before_call=True)
        self.overseer.oversee(self.b, owner_attributes='a', after_return=True)

    def b(self, k=1):
        self.a += k
        return k

### class A instantiation
a = A()

### lets perform some method calls
for k in range(3):
    print(a.b(k))

OUTPUT:
0
1
2

### Access to instance.overseer.history:
### output is a list of stats
>>>a.overseer.history

OUTPUT:
[OverseerHistoryItem(owner_class='A', owner_instance_id=4423806464, method='b', when='called', time=datetime.datetime(2024, 9, 26, 0, 12, 53, 778232), owner_attributes=None, args=(0,), kwargs={}, text=None, result=None),
 OverseerHistoryItem(owner_class='A', owner_instance_id=4423806464, method='b', when='returned', time=datetime.datetime(2024, 9, 26, 0, 12, 53, 778252), owner_attributes={'a': 1}, args=None, kwargs=None, text=None, result=None),
 OverseerHistoryItem(owner_class='A', owner_instance_id=4423806464, method='b', when='called', time=datetime.datetime(2024, 9, 26, 0, 12, 53, 778286), owner_attributes=None, args=(1,), kwargs={}, text=None, result=None),
 OverseerHistoryItem(owner_class='A', owner_instance_id=4423806464, method='b', when='returned', time=datetime.datetime(2024, 9, 26, 0, 12, 53, 778291), owner_attributes={'a': 2}, args=None, kwargs=None, text=None, result=None),
 OverseerHistoryItem(owner_class='A', owner_instance_id=4423806464, method='b', when='called', time=datetime.datetime(2024, 9, 26, 0, 12, 53, 778304), owner_attributes=None, args=(2,), kwargs={}, text=None, result=None),
 OverseerHistoryItem(owner_class='A', owner_instance_id=4423806464, method='b', when='returned', time=datetime.datetime(2024, 9, 26, 0, 12, 53, 778308), owner_attributes={'a': 4}, args=None, kwargs=None, text=None, result=None)]

### Access to globals stats
### output is a StatsClassRegistry
>>> Overseer.history

OUTPUT:  Sthis returns all history items from all registered methods and instances
    """

    registry = OverseerRegistry()
    history = OverseerHistoryDescriptor()

    def __init__(self, owner_instance) -> None:
        self.owner_instance = owner_instance
        owner_instance.overseer = self

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
            if isinstance(owner_attributes, str):
                owner_attributes = (owner_attributes,)

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
                    self.registry.append(OverseerHistoryIndex(len(self.__class__.history)))
                    self.__class__.history.append(dump)
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

                    self.registry.append(OverseerHistoryIndex(len(self.__class__.history)))
                    self.__class__.history.append(dump)
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
            instance._overseer = Overseer(instance)
            ### THIS CAUSES CONFLICT as Overseer instals itself in instance.overseer attribute

        return instance._overseer


def _decorate_class(cls, *args, **kwargs):

    old_init = cls.__init__

    def __init__(_self, *instance_args, **instance_kwargs):
        old_init(_self, *instance_args, **instance_kwargs)

        _self.overseer = Overseer(_self)

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
        def b(): # will NOT be overseen
        def c(): # will be overseen after return, and the result will be stored

    :param args:
    :param kwargs:
    :return: decorated class
    """
    if not kwargs and len(args) == 1 and isinstance(args[0], type):
        return _decorate_class(args[0])
    else:
        return partial(_decorate_class, *args[1:], **kwargs)
