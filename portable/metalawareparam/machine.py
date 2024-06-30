import os
import platform
import uuid
from dataclasses import dataclass, field, asdict
from hashlib import sha256


def mac(hex=True):
    if hex:
        return ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) for ele in range(0, 8 * 6, 8)][::-1])
    else:
        return uuid.getnode()


def memory(g=True, raise_nt=False):
    try:
        mem_bytes = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')  # e.g. 4015976448
        mem_gib = mem_bytes / (1024. ** 3)
        if g:
            return mem_gib
        else:
            return mem_bytes
    except AttributeError:
        if raise_nt:
            raise NotImplemented('Memory readout is not implemented outside Unix systems.')
        else:
            return None


def procesor():
    return platform.processor()


def system():
    return platform.system()


def machine_info():
    return {
        'node': platform.node(),
        'processor': platform.processor(),
        'system': platform.system(),
        'machine': platform.machine(),
        'mac': mac(),
        'memory': memory(g=True)
    }


def this_machine_hash():
    return Machine().sha256()


@dataclass
class Machine:
    node: str = field(default=platform.node(), init=False, repr=True)
    processor: str = field(default=platform.processor(), init=False, repr=True)
    system: str = field(default=platform.system(), init=False, repr=True)
    machine: str = field(default=platform.machine(), init=False, repr=True)
    mac: str = field(default=mac(), init=False, repr=True)
    memory: str = field(default=memory(g=True, raise_nt=False), init=False, repr=True)

    def to_dict(self):
        return asdict(self)

    def __hash__(self):
        return hash(self.to_dict())

    @property
    def string(self):
        return ''.join(tuple(str(p) for p in self.to_dict().values()))
