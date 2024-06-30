import json
import os

local_path = os.path.dirname(__file__)
store_file_name = 'db.json'
store_file_path = os.path.join(local_path, store_file_name)

class Void:
    def __repr__(self):
        return '<Void>'

void = Void()

def start_db():
    save_db(dict())


def save_db(j: dict) -> None:
    if not isinstance(j, dict):
        raise TypeError(f'Can only store type dict. Got {type(j)}.')
    with open(store_file_path, 'w') as f:
        f.write(json.dumps(j))


def read_db() -> dict:
    if not os.path.isfile(store_file_path):
        start_db()
        return dict()
    with open(store_file_path, 'r') as f:
        read = f.read()
        if not read:
            return dict()
        return json.loads(read)


def update_db(machine_hash, param_name, value) -> None:
    old = read_db()
    if machine_hash not in old:
        old[machine_hash] = dict()
    old[machine_hash].update({param_name: value})
    save_db(old)


def get_machine_params(machine_hash):
    db = read_db()
    return db.get(machine_hash)


def get_param(machine_hash, param_name, default=void):
    if machine := get_machine_params(machine_hash):
        if param_name in machine:
            return machine[param_name]
        elif default != void:
            return default
        else:
            raise ValueError(f'MetalAwareParam {param_name} not in store.')
    elif default != void:
        return default
    else:
        raise ValueError('This machine has no MetalAwareParam stored yet.')


def reset_db():
    save_db(dict())
