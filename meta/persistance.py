from functools import wraps
import logging
import time
from ptbutil.errors import DecorationError
from functools import partial
from ptbutil.func.decay import Decay
from metalawareparam import MetalAwareParam

handler = logging.StreamHandler()
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
handler.setLevel(10)
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(10)


class PersistanceError(Exception):
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
        raise PersistanceError(f'Function {fn.__name__} unable to persist with args: {args}, kwargs: {kwargs}')\
            from err
    return wrapper


def persist(arg):
    """
    This is a decorator.
    It can be used without arguments, in this case n will be 1
    or with a single argument which must be type int, to indicate value n.

    Decorated function will be performed n times if it throws an error during runtime
    before finally it throws a PersistanceError.
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


missing = object()

def machineaware_delay_persist(n=3, delay_max=10, delay_min=0):
    """
    This is a decorator.
    It must be used with parameters always.

    It delivers a wrapper for a decorated function (fn).
    Fn will be reperformed n times if it throws an exception of any kind before the exception is risen.

    There will delay implemented before the function is performed.
    The delay starts with delay_max value but asymptotically will be decreasing towards 0 each time exception is not thrown.
    If exception is thrown it will be asssumed that it was caused by timeout and predelay will be increased according to Delay protoclo.

    The implemented delay is machine aware. This means that if it works form a portable medium (usb-drive)
    it will be adjusted to the machine platform.
    This is achieved by storing the machine, fn, and delay parameters.

    """
    def decorator(fn):
        nonlocal delay_max
        nonlocal delay_min

        delay_max_map = MetalAwareParam(f"{fn.__name__}delay_max").retrieve(delay_max)
        delay_min_map = MetalAwareParam(f"{fn.__name__}delay_min").retrieve(delay_min)
        # decay_rate_map = MetalAwareParam(f"{fn.__name__}delay_decay_rate").retrieve(0.5)
        # po wczytaniu start i asmyptote rate powinno być zawsze wysokie = 0.5
        D = Decay(start=delay_max_map.value, asymptote=delay_min_map.value, rate=0.5)

        @wraps(fn)
        def wrapper(*args, **kwargs):
            predelay = D.deliver()  # this must be here and  not within the loop
            t0 = time.perf_counter()
            result = missing
            for n_persist in range(n):
                try:
                    logger.debug(f'Function {fn.__name__} persistance loop {n_persist} opened')
                    logger.debug(f'Functiion {fn.__name__} predelay {predelay}')
                    time.sleep(predelay)
                    result = fn(*args, **kwargs)
                    return result
                except Exception as err:
                    raise PersistanceError(
                        f'Function {fn.__name__} unable to persist with args: {args}, kwargs: {kwargs}') from err
                finally:
                    logger.debug(f'Function {fn.__name__} persistance loop {n_persist} closed')
                    if result != missing: # mam wynik
                        if n_persist > 0:  # result but not in the first loop
                            D.nudge(time.perf_counter() - t0)  # nudge to the successful time
                        else:  # mam wynik i to wpierwszym loopie
                            pass  # no nudge
                        delay_max_map.value = D.last_nudge
                        delay_min_map.value = D.asymptote
                    else:  # nie mam wyniku
                        if n_persist == n - 1:  # to ostatni loop ale nadal nie ma wyniku
                            D.nudge()  # nudge wg protokołu
                        else:
                            pass  # pójdzie następny loop

            raise PersistanceError(f'Function {fn.__name__} unable to persist with args: {args}, kwargs: {kwargs}')
        return wrapper
    return decorator


madpersist = machineaware_delay_persist  # alias
