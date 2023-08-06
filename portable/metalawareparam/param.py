
from .db_functions import update_db, get_param, void
from .machine import Machine
import atexit


class MetalAwareParam:
    def __init__(self, name: str, value=void, store_at_exit=True):
        self._name = None
        self.name = name
        self.value = value
        self.machine = Machine()
        if store_at_exit:
            atexit.register(self.store)

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, val: str) -> None:
        if not isinstance(val, str):
            raise TypeError('name must be type str')
        if self._name:
            raise ValueError('The name of the parameter had been set already.')
        self._name = val

    def retrieve(self, default=void):
        self.value = get_param(self.machine.string, self.name, default)
        return self

    def store(self):
        if self.value == void:
            raise ValueError('Parameter can not be stored as its value has not been set yet.')
        update_db(self.machine.string, self.name, self.value)
        return self
