
import yaml
from typing import Dict, Any
from ptbutil.iteration.dictwise import merge_2_dicts

class Config(object):
    def __init__(self, name=None):
        self._config_own_name = name or 'Config'

    def __getattr__(self, name: str) -> Any:
        return super().__getattribute__(name)

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any], name=None):
        config = cls(name)
        for k, v in config_dict.items():
            if isinstance(v, dict):
                v = Config.from_dict(v, name='.'.join((config._config_own_name, k)))
            config.__setattr__(k, v)
        return config

    @classmethod
    def from_yaml(cls, path):
        with open(path, 'r') as f:
            return Config.from_dict(yaml.load(f.read(), Loader=yaml.CLoader))

    @staticmethod
    def config_to_dict(val):
        if isinstance(val, Config):
            return {k: Config.config_to_dict(v) for k, v in val.__dict__.items() if k != '_config_own_name'}
        else:
            return val

    def as_dict(self):
        return Config.config_to_dict(self)

    def copy(self):
        return Config.from_dict(self.as_dict())

    def __repr__(self):
        return f'<{self._config_own_name}: {self.as_dict()}>'

    def __add__(self, other):
        self_ = self.as_dict()
        if isinstance(other, dict):
            pass
        elif isinstance(other, Config):
            other = other.as_dict()
        merged = merge_2_dicts(self_, other)
        return Config.from_dict(merged)

    def update(self, other):
        if isinstance(other, Config):
            other = other.as_dict()
        elif isinstance(other, dict):
            pass
        else:
            raise TypeError(f'Config can be updated with another Config object or dict type only')

        for k, v in other.items():
            no_attribute = None
            self_value = None

            try:
                self_value = getattr(self, k)
            except AttributeError:
                no_attribute = True

            if isinstance(v, dict):
                if isinstance(self_value, Config):
                    self_value.update(v)
                elif no_attribute:
                    setattr(self, k, Config(name='.'.join((self._config_own_name, k))).update(v))
                else:
                    raise ValueError(
                        f'Conflict while updating: {k}. Old and new Config attribute k are different type.')
            else:
                if isinstance(self_value, Config):
                    raise ValueError(
                        f'Conflict while updating: {k}. Old and new Config attribute k are different type.')
                else:
                    setattr(self, k, v)
        return self

    def __eq__(self, other):
        if isinstance(other, Config):
            other = other.as_dict()
        elif isinstance(other, dict):
            pass
        else:
            raise TypeError(f'Config can not be compared to {type(other)}.')
        return self.as_dict() == other