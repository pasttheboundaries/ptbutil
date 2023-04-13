import time
from functools import wraps
import logging

__all__ = ['log_timing', 'now', 'performance', 'print_timing', 'Stopper']


def log_timing(fn):
    """simple decorator logging timing at logging.info level"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        t1 = time.perf_counter()
        result = fn(*args, **kwargs)
        t2 = time.perf_counter()
        logging.info(f'Function {fn.__name__} timing: {str(t2-t1)}')
        return result
    return wrapper


def now(format=None):
    format = format or "%Y/%m/%d_%X"
    return time.strftime(format)


class perf_pool:
    """
    A pooler to test time performance of functions:
    Decorate function definition with: perf_pool.register
    Once perf_pool.run(*args, **kwargs) is called,
        all the pooled functions will be called with the passed arguments and timed, and results will be printed.

    Attributes:
        pool : a list of registered functions
        results : results of performance measurement
        iterations : int - default=1, to run the tested functions multiple times.
        decimal : int - number of numbers after float point to be shown at results printing.

    Methods:
        purge() - purges the pool
        reset() - resets all attributes to default
        register(fn: Function) - to be used as a decorator for a function definition,
         or as a method accepting function to be pooled
        run(*args, **kwargs) - runs and times all pooled functions.

    Caveats:
        Pooled functions will be called with the arguments passed to perf_pool.run(),
        so they have to have suiting call parameters.
    """
    pool = []
    results = dict()
    iterations = 1
    decimal = 4

    @staticmethod
    def purge():
        perf_pool.pool.clear()
        perf_pool.results.clear()

    @ staticmethod
    def reset():
        perf_pool.purge()
        perf_pool.iterations = 1
        perf_pool.decimal = 4

    @staticmethod
    def register(fn):
        perf_pool.pool.append(fn)
        return fn

    @staticmethod
    def run (*args, **kwargs):
        perf_pool.iterations = max(perf_pool.iterations, 1)

        for fn in perf_pool.pool:
            printout = f'testing {fn.__name__}'
            print (printout, end= '')

            current_iteration = 0

            t1 = time.perf_counter()
            while current_iteration < perf_pool.iterations:
                fn(*args, **kwargs)  # ignores reslults of the tested function
                current_iteration += 1
            t2 = time.perf_counter()
            total_t = t2 - t1
            mean_t = total_t / perf_pool.iterations
            perf_pool.results.update({fn: {'total_t': total_t,
                                           'mean_t': mean_t}})
            printout  = '\r' + ' '*len(printout) + '\r'
            print(printout, end ='')
        perf_pool._count_relative()
        perf_pool._pprint()

    @staticmethod
    def _count_relative():
        if not perf_pool.results:
            return
        rank = sorted(perf_pool.results.items(), key=lambda i: i[1]['total_t'])
        best_t = rank[0][1]['total_t']
        for res in rank:
            res[1]['relative'] = res[1]['total_t'] / best_t
        perf_pool.results = dict(rank)

    @staticmethod
    def _pprint():
        if not perf_pool.results:
            return
        for fn, res in perf_pool.results.items():
            print(f"""{fn.__name__} :
\r\ttotal time = {round(res['total_t'], perf_pool.decimal)}
\r\tmean time = {round(res['mean_t'], perf_pool.decimal)}
\r\trelative = {round(res['relative'], perf_pool.decimal)}""")



def performance(repetitions=1, mean=False):
    """Callable decorator.
    Output functions prints timing to stout. Can perform decorated fucnction multiple times and count mean timeing.
    Parameters:
        repetitions: int - number of repetitions
        mean: bool - weather to count mean timing. If False - total timing for all repetitions will be printed"""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            c = 0
            for _ in range(repetitions):
                t1 = time.perf_counter()
                result = fn(*args, **kwargs)
                t2 = time.perf_counter()
                c += t2-t1
            if mean:
                timing = c / repetitions
                tstring = 'performance mean time'
            else:
                timing = c
                tstring = 'performance total time'
            print(f'Function {fn.__name__}, at {repetitions} repetitions, {tstring}: {str(timing)}')
            return result
        return wrapper
    return decorator

def print_timing(fn):
    """simple decorator printing timing to stout"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        t1 = time.perf_counter()
        result = fn(*args, **kwargs)
        t2 = time.perf_counter()
        print(f'Function {fn.__name__} timing: {str(t2-t1)}')
        return result
    return wrapper

class StopperRecord:
    def __init__(self, current, total, lap, comment, decimal=3, oneline=False):
        self.current = current
        self.total = total
        self.lap = lap
        self.comment = comment
        self.decimal = decimal
        self._oneline = oneline

    def _comment(self):
        return (f'time_stamp:{self.current},'
                f' total:{str(round(self.total, self.decimal))},'
                f' lap:{str(round(self.lap, self.decimal))},'
                f' comment:{self.comment}')

    def show(self):
        if self._oneline:
            print('\r\x1b[1K', self._comment(), end='')
        else:
            print(self._comment())

    def __repr__(self):
        return f'<StopperRecord> time_stamp:{self.current}, ' \
               f'total:{str(round(self.total, self.decimal))}, ' \
               f'lap:{str(round(self.lap, self.decimal))}, ' \
               f'comment:{self.comment}'



class Stopper:
    """Stopper object
    It calculates time passed between moments it was called:
    Methods:
        __call__(comment=None) - starts, stops and collect half times with the comment.
        status() - returns halftimes and lap times as a string
        current(comment=None) - returns a single line of status '{halftime} : {lap time}, : {comment}'
        start() and stop() work as a call, and are provided to perform default activities of a stopper."""
    FORMAT = "%Y/%m/%d %H:%M:%S"
    def __init__(self, name=None, decimal=1, oneline=False):
        """
        name: str,
        decimal: int - number of decimal places to show"""
        self.decimal = decimal
        self.name = name or 'Stopper'
        self.register = dict()
        self.start_time = None
        self.oneline = oneline

    def _capture(self):
        current = time.perf_counter()
        total = self._total(current)
        lap = self._lap_time(total)
        return current, total, lap

    def _record(self, comment=None):
        current, total, lap = self._capture()
        register_no = len(self.register)
        self.register[register_no] = StopperRecord(current, total, lap, comment, oneline=self.oneline)
        if len(self.register) == 1:
            self.start_time = current
        return self.register[register_no]

    def _lap_time(self, current_total):
        last_record = self.register.get(len(self.register) - 1, None)
        if last_record:
            last_total = last_record.total
            return current_total - last_total
        else:
            return 0

    def _total(self, current):
        if self.start_time:
            return current - (self.start_time or 0)
        else:
            return 0

    def start(self, comment=None):
        return self._record(comment=comment)

    def stop(self, comment=None):
        return self._record(comment=comment)

    def __call__(self, comment=None):
        return self._record(comment=comment)

    def current(self, comment=None):
        current, total, lap = self._capture()
        n_lap = self.register.keys()[-1]
        return f'lap:{n_lap}, total:{total}, laptime:{lap}'

    def status(self, decimal=None):
        """decimal: int - number of decimal places to show"""
        decimal = decimal or self.decimal
        stat = '\n'.join(
            [self.name] + [f'{str(key)}: {time.strftime(Stopper.FORMAT, time.localtime(value.current))} '
                           f': {str(round(value.total, decimal))} '
                           f': {str(round(value.lap, decimal))} '
                           f': {value.comment}' for
                           key, value in self.register.items()])
        return stat

    def show(self):
        print(self.status())

    def __str__(self):
        return self.status()

