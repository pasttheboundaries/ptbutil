from functools import partial
from .classes import Overseer
from .exceptions import DecorationError


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


