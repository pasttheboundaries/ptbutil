"""

This script provicdes methods to bulid application data library from incoming input data.
A json file is kept to store the data. This allows a dev to quickly store client names or values for later use.

A MetaJStore is not intended to substitute local database,
 but rather to alleviate dev work by collecting meta_data both at ddebugging and during production.

Usage:
Whenever there is a need for collecting of client idiomatic names or other data,
the following code can be used:
metastore['my_key'].add(value).dump()
this will add the value to the stored collection AND remove duplicates in the collection (as per set behaviour)

In general MetaJstor.__getitem__ will return a DictItemProxy.
metastore['my_key'] -> <DictItemProxy value=[1,2,3...]>

DictItemProxy has 5 methods:
    add(element): adds element to the stored collection and makes sure duplicates are removed (as in set)
        OR starts the stored collection as a set and adds the element
    add_many(elements_iterable): as above but takes an iterable as an argument
    append(element): appends element to the stored collection OR starts the stored collection as a list and appends
    extend(elements_iterable): extends the stored collection OR starts it as list and extends
    update({k:v}): updates the stored collection OR starts the stored collection as a dict and updates it with passeditems

so recording can be performed by calling one of the above:
metastore['my_key].append(element)
    There is NO NEED to asign the intended data structure first like in:
        metastore['mykey'] = []
        metastore['mykey'].append(e).

All the above methods of DictItemProxy retrun the parenting MetaJStore instance, so further .dump() can be used.
metastore['my_key].append(element).dump()

To get the stored collection use property value
metastore['my_key'].value -> [1,2,3,4,5]


# importing
from metajsstore import MetaJStore

# instantiation
# it can be any path but it is also reasonable to keep one MetaJsStore per project.
metastore = MetaJsStore(filepath)

# reading record
metastore['my vars'].value - to retireve the recorded colelction

# creating new record (as per dictionary protocl)
metastore['client_names'] = dict(clinet_names_collection)
OR
metastore['client_names'].update(dict(clinet_names_collection))

metastore.dump()
# this will dump the collection into json file.
# Also: this will be also called at system forced exit

"""


from typing import Collection, Hashable, Mapping
import pandas as pd
import os
import json
import atexit
from threading import Lock
from ahdclinicaldash.paths import META_JS_PATH


update_lock = Lock()
dump_lock = Lock()
missing = object()


def init_meta_js_store(filepath=None):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            s = json.loads(f.read())
    except (FileNotFoundError, json.JSONDecodeError):
        s = {}
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(json.dumps(s))
    return s


def dump_store(path, store):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(store))


class DictItemProxy:

    def __init__(self, metajstore, origin_dict, key):
        self.metajstore = metajstore
        self.origin_dict = origin_dict
        self.key = key
        self.old = origin_dict.get(key, missing)

    @property
    def value(self):
        return self.origin_dict[self.key]

    def update(self, __m: Mapping, **kwargs):
        if isinstance(self.old, dict):
            self.old.update(__m, **kwargs)
            d = self.old
        elif self.old == missing:
            d = dict()
            d.update(__m, **kwargs)
        else:
            raise TypeError(f'Could not use method unable on the stored object type {type(self.old)}')
        self.reascribe(d)

    def add(self, element):
        self.append(element, _method='add')
        self.reascribe(set(self.origin_dict[self.key]))
        return self.metajstore

    def add_many(self, collection):
        collection = set(collection)
        if isinstance(self.old, list):
            for o in collection:
                self.old.append(o)
            d = list(set(self.old))
        elif self.old == missing:
            d = list(set(collection))
        else:
            raise TypeError(f'Could not use method add on the stored object type {type(self.old)}')
        self.reascribe(d)
        return self.metajstore

    def append(self, element, _method='append'):
        if isinstance(self.old, list):
            self.old.append(element)
            d = self.old
        elif self.old == missing:
            d = list()
            d.append(element)
        else:
            raise TypeError(f'Could not use method {_method} on the stored object type {type(self.old)}')
        self.reascribe(d)
        return self.metajstore

    def extend(self, collection):
        if isinstance(self.old, list):
            self.old.extend(collection)
            d = self.old
        elif self.old == missing:
            d = list()
            d.extend(collection)
        else:
            raise TypeError(f'Could not use method extend on the stored object type {type(self.old)}')
        self.reascribe(d)
        return self.metajstore

    def reascribe(self, val):
        self.origin_dict[self.key] = val

    def __repr__(self):
        if len(s := str(self.value).split(',')) > 10:
            close = s[0].startswith('{') and '}' or ']'
            val = f"{','.join(s[:10])} {'...'} {close}"
        else:
            val = self.value

        return f'<DictItemProxy value: {val}>'


class MetaJStore:

    """
    StoreHolder descriptor gurantees always the most recent version of store is retrieved
    """

    def __init__(self, file_path: str):
        self.filepath = file_path
        self.store = init_meta_js_store(file_path)

    def __getitem__(self, item):
        return DictItemProxy(self, self.store, item)

    def __setitem__(self, key, value):
        if not isinstance(value, (dict, list, tuple, set)):
            raise TypeError('MetaJStore can store only native python data structures.')
        if isinstance(value, (set, list)):
            value = list(set)
        with update_lock:
            return self.store.update({key: value})

    def as_dict(self):
        return self.store

    def __iter__(self):
        return (it for it in self.store.items())

    def dump(self):
        with dump_lock:
            return dump_store(self.filepath, store=self.store)
