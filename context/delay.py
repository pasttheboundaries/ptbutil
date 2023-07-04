import random
from typing import Optional, Union, Callable
import time


class Delay:
    """
    this is a context manager of delay
    At context exit it implements delay as defined at instantiation

    t: float - time in seconds or a callable returning float
    sd: float - standard deviation of variability distribution as gaussian
    """
    def __init__(self, t: Union[float, Callable], sd: Optional[float] = None):
        self.t = t
        self.sd = sd

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if callable(self.t):
            time.sleep(self.t())
        else:
            if self.sd:
                time.sleep(max(0, random.gauss(self.t, self.sd)))
            else:
                time.sleep(self.t)

