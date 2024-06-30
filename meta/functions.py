import inspect
import logging
from inspect import signature
from typing import Optional, Any, Container
from functools import wraps


def signature_parameters(obj):
    return tuple(signature(obj).parameters)


spar = signature_parameters  # alias


def in_module(module_):
    module_name = module_.__name__
    functions = inspect.getmembers(module_, inspect.isfunction)
    classes = inspect.getmembers(module_, inspect.isclass)
    #functions = [(fn_name, fn) for fn_name, fn in functions if fn.__module__ == module_name]
    #classes = [(class_name, cls) for class_name, cls in classes if cls.__module__  == module_name]
    return {'classes': classes, 'functions': functions}





