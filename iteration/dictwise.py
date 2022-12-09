import string
import logging


class dicta(dict):
    """this is a dictionary with getattr and setattr methods implemented"""

    INVALID_PUNCTUATION = ''.join([char for char in string.punctuation if char != '_'])

    def __init__(self, __d__=None, **kwargs):
        """can not accept key_word argument with __d__ key."""
        if __d__:
            if isinstance(__d__, (dict, dicta)):
                self.update(__d__)
            else:
                raise TypeError('Passed object must by type dict or dicta.')

        if kwargs:
            self.update(kwargs)

    def from_namespace(self, namespace):
        for k, v in namespace.__dict__.items():
            if isinstance(k, str):
                self.update({k: v})
            else:
                logging.warning('Invalid key. Key must be type str.')


    def update(self, __d__):
        if not isinstance (__d__, (dict, dicta)):
            raise TypeError('Can update dicta only with dict or dicta.')
        for k, v in __d__.items():
            self._validate_key(k)
            super().update({k: v})


    def _validate_key(self, key):
        if not isinstance(key, str):
            raise TypeError(f'Key must be type str. Passed {key}.')
        if key[0].isdigit():
            raise ValueError(f'Key can not start with a digit. Passed {key}.')
        if any([char in self.INVALID_PUNCTUATION for char in key]):
            raise ValueError(f'Punctuation characters can not be used in keys. Passed {key}.')

    def __getattr__(self, item):
        return self[item]

    def __setattr__(self, key, value):
        self._validate_key(key)
        self[key] = value


def sort_by_value(dictionary: dict) -> dict:
    return {k: v for k, v in sorted(dictionary.items(), key=lambda item: item[1])}


def merge_2_dicts(a: dict, b: dict, keep='a'):
    """merges 2 nested dicts
    If there is a value collision use keep parameter to indicate the dictionary with priority"""
    for key in b.keys():
        if key in a.keys():
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge_2_dicts(a[key], b[key])
            elif a[key] == b[key]:
                pass
            else:
                if keep == 'a':
                    pass
                else:
                    a[key] = b[key]
        else:
            a[key] = b[key]
    return a
