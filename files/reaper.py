"""
 this module is used by package  amms

 There is a copy of this module in general scope

"""
import os
import json
import datetime


def make_dir(path):
    try:
        os.mkdir(path)
    except FileExistsError:
        pass
    except FileNotFoundError:
        raise ValueError(f'path not found {path}')
    else:
        return True


class Reaper:
    def __init__(self, dirpath=None, filename=None, dump_at=10):
        self.dirpath = dirpath or os.getcwd()
        make_dir(self.dirpath)
        self.filename = filename or 'reaped.json'
        self.filepath = os.path.join(self.dirpath, filename)
        if not os.path.isfile(self.filepath):
            self.write([])
        else:
            collected = self.read()
            assert isinstance(collected, list) and all(isinstance(d, dict) for d in collected)
        self.dump_at = dump_at
        self.collection = []

    def validate_obj(self, obj):
        if not isinstance(obj, dict):
            raise TypeError(f'Expected type dir, got type {type(obj)} .')
        return obj

    def validate_extension(self, ext):
        if not isinstance(ext, (list, tuple)):
            raise TypeError(f'Expected type list or tuple, got type {type(ext)} .')
        return ext

    def read(self):
        with open(self.filepath, 'r', encoding='utf-8') as f:
            return json.loads(f.read())

    def write(self, obj):
        """
        writes list of dicts into the file
        :param obj:
        :return:
        """
        assert isinstance(obj, list) and all(isinstance(d, dict) for d in obj)
        with open(self.filepath, 'w', encoding='utf-8') as f:
            f.write(json.dumps(obj))
            return True

    def append(self, obj: dict):
        """
        appends object to the file
        :param obj:  dict
        :return: None
        """
        if not isinstance(obj, dict):
            obj = {0: obj}
        obj = self.validate_obj(obj)
        obj.update({'reaped': datetime.datetime.now().isoformat()})
        old = self.read()
        old.append(obj)
        self.write(old)

    def collect(self, obj):
        """
        appends object to self.collection
        if collection is longer than dump_at: dumps collection t=into the file
        :param obj:
        :return: None
        """
        obj = self.validate_obj(obj)
        obj.update({'reaped': datetime.datetime.now().isoformat()})
        self.collection.append(obj)
        if len(self.collection) >= self.dump_at:
            self.dump()
            self.collection.clear()

    def dump(self):
        """
        dumps collection
        :return: None
        """
        old = self.read()
        old.extend(self.collection)
        self.write(old)

    def already_reaped(self, key, value) -> bool:
        """
        checks if obj with particular key and value already has been collected
        :param key: Hashable
        :param value: Any
        :return: bool
        """
        reaped = self.read()
        for pt in reaped:
            if pt.get(key) == value:
                return True
        return False


