from functools import wraps
from collections.abc import Iterable
import logging
#from meta import GlobalLoggerManager, meta_indentation_head
#from .. import config
from ptbutil.errors import DecorationError
from functools import partial

handler = logging.StreamHandler()
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
handler.setLevel(10)
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(10)


class PersistanceException(Exception):
    pass


def persist_decorator(fn, _n):
    @wraps(fn)
    def wrapper(*args, **kwargs):

        for n_persist in range(_n):
            try:
                logger.debug(f'Function {fn.__name__} persistance loop {n_persist} opened')
                result = fn(*args, **kwargs)
                return result
            except Exception as e:
                err = e
            finally:
                logger.debug(f'Function {fn.__name__} persistance loop {n_persist} closed')
        raise PersistanceException(f'Function {fn.__name__} unable to persist with args: {args}, kwargs: {kwargs}')\
            from err
    return wrapper


def persist(arg):
    """
    This is a decorator.
    It can be used without arguments, in this case n will be 1
    or with a single argument which must be type int, to indicate value n.

    Decorated function will be performed n times if it throws an error during runtime
    before finally it throws a PersistanceException.
    Last error will be propagated in traceback.
    """
    if callable(arg):
        _n = 1
        return persist_decorator(arg, _n)
    elif isinstance(arg, int):
        _n = arg
        return partial(persist_decorator, _n=arg)
    else:
        raise DecorationError from TypeError('persist can accept type int as parameter only')

