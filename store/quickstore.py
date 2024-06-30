"""

A QuickStore is not intended to substitute local database,
 but rather to provide low volume, quick acces single file data store.

Usage:
store_path = '~/data/qstore'
qs = QuickStore(store_path)
qs['my_key'].add(value).dump()
this will add the value to the stored 'my_key' collection  (set in this case) AND remove duplicates in the collection (set behaviour)

In general QuickStore.__getitem__ will return a CollectionProxy.
qs['my_key'] -> <CollectionProxy value=[1,2,3...]>

CollectionProxy has 5 methods:
    add(element): adds element to the stored collection and makes sure duplicates are removed (as in set)
        OR starts the stored collection as a set and adds the element
    add_many(elements_iterable): as above but takes an iterable as an argument
    append(element): appends element to the stored collection OR starts the stored collection as a list and appends
    extend(elements_iterable): extends the stored collection OR starts it as list and extends
    update({k:v}): updates the stored collection OR starts the stored collection as a dict and updates it with passeditems

so recording can be performed by calling one of the above:
qs['my_key].append(element)
    There is NO NEED to asign the intended data structure first like in:
        qs['mykey'] = []
        qs['mykey'].append(e).

All the above methods of CollectionProxy retrun the parenting QuickStore instance, so further .dump() can be used.
qs['my_key].append(element).dump()

To get the stored collection use property value
qs['my_key'].value -> [1,2,3,4,5]


# importing
from quickstore import QuickStore

# instantiation
# it can be any path but it is also reasonable to keep one QuickStore per project.
qs = QuickStore(filepath)

# reading record
qs['my vars'].value - to retireve the recorded colelction

# creating new record (as per dictionary protocl)
qs['client_names'] = dict(clinet_names_collection)
OR
qs['client_names'].update(dict(clinet_names_collection))

qs.dump()
# this will dump the collection into json data.
# Also: this will be also called at system forced exit

"""


from typing import Mapping, Union
import json, atexit, pathlib
from threading import Lock



update_lock = Lock()
dump_lock = Lock()
missing = object()


def init_quick_store(filepath=None):
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


class CollectionProxy:

    def __init__(self, quickstore, origin_dict, key):
        self.quickstore = quickstore
        self.origin_dict = origin_dict
        self.key = key
        self.old = origin_dict.get(key, missing)

    @property
    def value(self):
        return self.origin_dict[self.key]

    def update(self, m: Mapping={}, **kwargs):
        if isinstance(self.old, dict):
            self.old.update(m, **kwargs)
            d = self.old
        elif self.old == missing:
            d = dict()
            d.update(m, **kwargs)
        else:
            raise TypeError(f'Could not use method update on the stored object type {type(self.old)}')
        self.reascribe(d)
        return self.quickstore

    def add(self, element):
        self.append(element, _method='add')
        self.reascribe(set(self.origin_dict[self.key]))
        return self.quickstore

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
        return self.quickstore

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
        return self.quickstore

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
        return self.quickstore

    def reascribe(self, val):
        self.origin_dict[self.key] = val

    def __repr__(self):
        if len(s := str(self.value).split(',')) > 10:
            close = s[0].startswith('{') and '}' or ']'
            val = f"{','.join(s[:10])} {'...'} {close}"
        else:
            val = self.value

        return f'<CollectionProxy value: {val}>'


def get_absolute_path(p: Union[str, pathlib.Path]):
    if '~' in str(p):
        p = str(p).replace('~', str(pathlib.Path.home()))
    p = str(pathlib.Path(p).absolute())
    return p


class QuickStore:

    """
    QuickStore class
    """

    def __init__(self, file_path: str):
        self.filepath = get_absolute_path(file_path)
        self.store: dict = init_quick_store(file_path)
        atexit.register(self.dump)

    def __getitem__(self, item):
        return CollectionProxy(self, self.store, item)

    def __setitem__(self, key, value):
        if not isinstance(value, (dict, list, tuple, set)):
            raise TypeError('QuickStore can store only native python data structures.')
        if isinstance(value, (set, list)):
            value = list(set)
        with update_lock:
            return self.store.update({key: value})

    def __del__(self):
        return self.dump()

    def as_dict(self):
        return self.store

    def __iter__(self):
        return (it for it in self.store.items())

    def dump(self):
        with dump_lock:
            return dump_store(self.filepath, store=self.store)
