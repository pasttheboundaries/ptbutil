
import yaml

class Config:
    def __init__(self, config_dict):
        for k, v in config_dict.items():
            self.__setattr__(k, v)

    @classmethod
    def from_yaml(cls, path):
        with open(path, 'r') as f:
            return Config(yaml.load(f.read(), Loader=yaml.CLoader))