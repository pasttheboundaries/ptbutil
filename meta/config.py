
import yaml


class Config:
    @classmethod
    def from_dict(cls, config_dict):
        config = cls()
        for k, v in config_dict.items():
            config.__setattr__(k, v)
        return config

    @classmethod
    def from_yaml(cls, path):
        with open(path, 'r') as f:
            return Config(yaml.load(f.read(), Loader=yaml.CLoader))
