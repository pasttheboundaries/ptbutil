import pandas as pd
import string
import random
import numpy as np
from ptbutil.debug import FuncPooler


ASCII_CONSONANTS = 'bcdfghjklmnpqrstvwxz'
ASCII_VOWELS = 'aoieuy'
sting_max_len = 10


def register_pool():
    @FuncPooler
    def string_column(max_len=sting_max_len, i=1):
        return (random.choice(string.ascii_uppercase) +
                ''.join(random.choices(string.ascii_lowercase, k=random.randint(1, max_len - 1))) \
                for _ in range(i))

    @FuncPooler
    def float_column(i=1):
        return np.array(np.random.rand(i))

    @FuncPooler
    def int_column(i=1):
        return np.array(np.random.randint(0, 10, i))


def random_df(i, c):
    assert type(i) == int and type(c) == int, 'both passed arguments must be integers.'
    register_pool()
    df = pd.DataFrame({col: FuncPooler.random_pool(c)[col](i=i) for col in range(c)}, index=range(i))
    df.columns = [str(col) for col in df.columns]
    return df


def memorable_string(length=2):
    new = []
    for i in range(length):
        if i%2 == 0:
            new.append(random.choice(ASCII_CONSONANTS))
        else:
            new.append(random.choice(ASCII_VOWELS))
    return ''.join(new)


def memorable_string_stamp(blocks=5):
    return '_'.join([memorable_string(4) for _ in range(blocks)])

