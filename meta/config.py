"""
this module provides advanced PolyConfig class
"""

import os
import re
import yaml
from string import ascii_letters, digits
from typing import Dict, Any, Optional
from ptbutil.iteration.dictwise import merge_2_dicts
from functools import wraps
from string import punctuation


def default_values_parser(val: str):
    if isinstance(val, str):
        lower = val.lower()
        if val.isdigit():
            return int(val)
        elif lower == 'true':
            return True
        elif lower == 'false':
            return False
        elif lower == 'none':
            return None
        elif lower == 'null':
            return None
        elif re.fullmatch(r'-?\d+[.]\d+', val):
            return float(lower)
        else:
            pass
    return val


def default_values_unparsed(val: str):
    return val


def validate_polyconfig_key(key: str):
    if key[0].isdigit():
        raise KeyError(f'PolyConfig variable name can not start with a digit: {key}')
    elif key[0] in punctuation:
        raise KeyError(f'PolyConfig variable name can not start with a punctuation: {key}')


def retrieve_env_variables(prefix: str = Optional[None]) -> dict:
    if prefix:
        return {k: v for k, v in os.environ.items() if k.startswith(prefix)}
    else:
        return dict(os.environ)


def local_yaml_path(cwd=None):
    cwd = cwd or os.getcwd()
    config = os.path.join(cwd, 'config.yaml')
    configuration = os.path.join(cwd, 'configuration.yaml')
    if os.path.isfile(config):
        return config
    elif os.path.isfile(configuration):
        return configuration
    else:
        return None


def dotsplit_k_v(k, v):
    k, rest = k.split('.', 1)
    return k, dotsplit_dict_keys({rest: v})


def dotsplit_dict_keys(d: dict) -> dict:
    """
    ammends dictrionary keys so:
    {'a.b': 1}
    becomes:
    {'a': {'b': 1}

    any length of the original keys is allowed:
    eg: 'a.b.c.d'

    :param d: dict
    :return: dicr
    """

    new = dict()
    for k, v in d.items():
        if '.' in k:
            nk, nv = dotsplit_k_v(k, v)
            new.update({nk: nv})
        else:
            new[k] = v
    return new


def validate_posix_variable_name(var: str):
    valid = set(ascii_letters + digits + '_')
    if any(l not in valid for l in var):
        raise ValueError(f'Variable name {var} is POSIX incompatible. Valid characters are ASCII characters. ')
    if var[0].isdigit():
        raise ValueError(f'Variable name {var} is POSIX incompatible. Digit can not be the first character. ')
    return var


def validate_config_value_type(val):
    if not isinstance(val, (str, float, int, bool)):
        raise TypeError(f'Config value must be one of type str, int, float or bool. Got {type(val)}')
    return val


def validate_flat_dict(d: dict):
    for k, v in d.items():
        validate_posix_variable_name(k)
        validate_config_value_type(v)
    return d


def flatten_nested_dict(d: dict):
    new = dict()
    for k, v in d.items():
        try:
            validate_config_value_type(v)
            new[k] = v
        except TypeError:
            if isinstance(v, dict):
                v = flatten_nested_dict(v)
                for vk, vv in v.items():
                    new['_'.join((k, vk))] = vv

            else:
                raise TypeError(f'Could not flatten the dict. '
                                f'Invalid type {type(v)}. '
                                f'Expected one of str, int, float, bool, dict.')
    return new


class Config(object):
    """
       Config object is designed to carry variables and constants in app environment


       Instantiation
       - optionally requires name. Default is Config.
            Name is stored as _config_own_name variable and serves for string representation of the config instance.
       - values_parser instantiation argument allows to pass a callable that parses string values.
            This migt be usefull when passing variables from evironment. Environment variables are always type str.
            default_values_parser can be used.


       Config works both as an object with attributes and subscriptable dict:
           conf.b == conf['b']
           -> True

       Regular python variable name restrictions apply:
           config['1_first'] = 1
           -> ValueError: Variable name 1 is POSIX incompatible. Digit can not be the first character.


       config.auto() -> returns Config instance
           conf = Config()
           conf.auto()
           1. Looks for config.yaml or configuration.yaml in cwd (os.getcwd())
           if present - updates self from the data.
           2. searches environment for variables and adds them to config_temp.
           If same name variables have been predefined in yaml data (step 1), they will be overriden.
           Updating is made in plase (as in bult-in dict.update). Also returns the config.

           When performing method auto(), and instance name had been defined at its instantiation:
           conf = Config('MYAPP')
           the enviroment variables starting with this name (or name followed by uderscore):
           'MYAPPVARIABLE_KEY' or 'MYAPP_VARIABLE_KEY'
           will be included in the update.

       os.environ['MYAPP_NUMBER'] = 3
       conf = Config('MYAPP')
       conf.auto()
       conf.MYAPP_NUMBER
       -> 3

       config.auto(env=True, yaml=True) is the most suitable for automatic update
       """

    DEFAULT_CONFIG_OWN_NAME = 'Config'
    _CLASS_OWN_KEYS = ('values_parser', '_config_own_name')

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            other = other.as_dict()
        elif isinstance(other, dict):
            pass
        else:
            raise TypeError(f'{self.__class__.__name__} can not be compared to {type(other)}.')
        return self.as_dict() == other

    def __init__(self, name=None, values_parser=None):
        self._config_own_name = name or self.DEFAULT_CONFIG_OWN_NAME
        self.values_parser = values_parser or default_values_unparsed

    def __getattr__(self, name: str) -> Any:
        return super().__getattribute__(name)

    def __getitem__(self, item) -> Any:
        return self.__getattr__(item)

    def __repr__(self):
        return f'<{self._config_own_name}: {self.as_dict()}>'

    def __setitem__(self, key, value) -> None:
        self.__setattr__(key, value)

    def __setattr__(self, k, v):
        validate_posix_variable_name(k)
        if not k in self._CLASS_OWN_KEYS:
            v = self.values_parser(v)
        super().__setattr__(k, v)


    def as_dict(self):
        return {k: v for k, v in self.__dict__.items() if k not in self._CLASS_OWN_KEYS}

    def auto(self, include_env=True, include_yaml=True):
        """
        autmatically updates Config instance
        :param include_env: searches os.environ for variables
        :param include_yaml: searches for config.yaml in cwd

        File reading is performed first so environment variables will override the data stored ones.

        :return: updated config
        """

        config_yaml_path = local_yaml_path()
        if include_yaml and config_yaml_path:
            conf_temp = self.__class__.from_yaml(config_yaml_path)
            self.update(conf_temp)

        if include_env:
            env_conf_temp = self.__class__.from_environment(self._config_own_name)
            self.update(env_conf_temp)

        return self

    @classmethod
    def autorefresh_incjected(cls, fn: callable):
        """decorator for a function that takes PolyConfig as one of the arguments.
        config.auto() will be called on config before passing to the decorated callable"""

        @wraps(fn)
        def wrapper(*args, **kwargs):
            for arg in args:
                if isinstance(arg, cls):
                    arg.auto()
            for k, v in kwargs.items():
                if isinstance(v, cls):
                    v.auto()
            return fn(*args, **kwargs)

        return wrapper

    def copy(self):
        return self.__class__.from_dict(self.as_dict())

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any], name=None, flatten=True):
        config = cls(name)
        if flatten:
            config_dict = flatten_nested_dict(config_dict)
        for k, v in config_dict.items():
            validate_posix_variable_name(k)
            validate_config_value_type(v)
            config.__setattr__(k, v)
        return config

    @classmethod
    def from_yaml(cls, path, name=None):
        with open(path, 'r') as f:
            return cls.from_dict(yaml.load(f.read(), Loader=yaml.CLoader), name=name, flatten=True)

    @classmethod
    def from_environment(cls, variable_prefix=None):
        """
        :param variable_prefix:
            if given - only env vars starting with the prefix will be included
        :return:
        """
        conf_temp = cls(variable_prefix)
        if variable_prefix == cls.DEFAULT_CONFIG_OWN_NAME:
            variable_prefix = None
        conf_temp.update(retrieve_env_variables(variable_prefix))
        return conf_temp

    def update(self, other):
        if isinstance(other, self.__class__):
            other = other.as_dict()
        elif isinstance(other, dict):
            pass
        else:
            raise TypeError(f'{self.__class__.__name__} '
                            f'can be updated with another {self.__class__.__name__} object or dict type only')

        for k, v in other.items():
            validate_posix_variable_name(k)
            validate_config_value_type(v)
            # v = self.values_parser(v)
            setattr(self, k, v)
        return self


class PolyConfig(Config):
    """
    PolyConfig object is designed to carry variables and constants in app environment

    WARNING:
        PolyConfig is not compatible with POSIX variables.
        POSIX does not allow . (dot) to be a part of a variable name.


    Instantiation optionally requires name. Default is PolyConfig.
    Name is stored as _config_own_name variable and serves for string representation of the config instance.

    PolyConfig allows for nesting
    d = {'a': 1, 'b': {'c':2}}
    conf = PolyConfig.from_dict(d)
    conf.b.c
    -> 2

    PolyConfig works both as a nested object and subscriptable dict:
    conf.b.c == conf['b']['c']
    -> True

    Regular python variable name restrictions apply:
    config['1_first'] = 1
    -> ValueError: PolyConfig variable name can not start with a digit: 1_first


    config.auto() -> returns PolyConfig instance
    conf = PolyConfig()
    conf.auto()
    1. Looks for config.yaml or configuration.yaml in cwd (os.getcwd())
    if present - creates config_temp = PolyConfig.from_yaml(path)
    if not - creates an empty config_temp = PolyConfig()
    2. searches environment for variables and adds them to config_temp.
    If same name variables have been predefined in yaml data (step 1), they will be overriden.
    but in this case:
    performs conf = conf.update(config_temp)  : overrides old variables and adds new.
    As the result the primary conf object is updated.

    When performing method auto(), and instance name had been defined at its instantiation:
    conf = PolyConfig('MYAPP')
    the enviroment variables starting with this name (or name followed by uderscore):
    'MYAPPVARIABLE_KEY' or 'MYAPP_VARIABLE_KEY'
    will be included in the update.
    Still the varable name in config will be stripped of this name:

    os.environ['MYAPP_NUMBER'] = 3
    conf = PolyConfig('MYAPP')
    conf.auto()
    conf.NUMBER
    -> 3
    conf.MYAPP_NUMBER
    -> AttributeError

    if environment variable is defined with dots it will become confing nested variable

    config.auto(env=True, yaml=True) is the most suitable for automatic update
    """

    DEFAULT_CONFIG_OWN_NAME = 'PolyConfig'

    def __add__(self, other):

        if isinstance(other, dict):
            pass
        elif isinstance(other, self.__class__):
            other = other.as_dict()
        else:
            raise TypeError(f'Could not add {type(other)} to {self.__class__.__name__}.')
        merged = merge_2_dicts(self.as_dict(), other)
        return self.__class__.from_dict(merged, name=self._config_own_name)

    def __setitem__(self, key, value) -> None:
        validate_polyconfig_key(key)
        self.update({key: value})

    def as_dict(self):
        return self._config_to_dict(self)

    def _config_to_dict(self, conf):
        if isinstance(conf, self.__class__):
            return {k: self._config_to_dict(v) for k, v in conf.__dict__.items() if k not in self._CLASS_OWN_KEYS}
        else:
            return conf

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any], name=None):
        config = cls(name)
        for k, v in config_dict.items():
            if isinstance(v, dict):
                v = cls.from_dict(v, name='.'.join((config._config_own_name, k)))
            config.__setattr__(k, v)
        return config


    def update(self, other):
        if isinstance(other, self.__class__):
            other = other.as_dict()
        elif isinstance(other, dict):
            pass
        else:
            raise TypeError(f'{self.__class__.__name__} '
                            f'can be updated with another {self.__class__.__name__} object or dict type only')

        other = dotsplit_dict_keys(other)

        for k, v in other.items():
            no_attribute = None
            self_value = None

            try:
                self_value = getattr(self, k)
            except AttributeError:
                no_attribute = True

            if isinstance(v, dict):
                if isinstance(self_value, self.__class__):
                    self_value.update(v)
                elif no_attribute:
                    setattr(self, k, self.__class__(name='.'.join((self._config_own_name, k))).update(v))
                else:
                    raise ValueError(
                        f'Conflict while updating: {k}. Old and new PolyConfig attribute {k} are different type.')
            else:
                if isinstance(self_value, self.__class__):
                    raise ValueError(
                        f'Conflict while updating: {k}. Old and new PolyConfig attribute {k} are different type.')
                else:
                    try:
                        validate_polyconfig_key(k)
                        setattr(self, k, self.values_parser(v))
                    except KeyError:
                        pass
        return self