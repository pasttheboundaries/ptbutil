"""
This is package for portable scripting

If a piece of code is to be run from a portable medium like pendrive
Sometimes internal parameters of the code depend on the machine it is run on

This package delivers dataclass MetalAwareParam as well as some other functionality
MetalAwareParam needs name at instantiation
value can be set at instantiation or later

MetalAwareParam.store - stores param.value in the internal store under this machine key
MetalAwareParam.retrieve retrieves value from the store if previously stored.
Retrieved value depends on the machine it is attempted to retrieve on

"""
from .param import MetalAwareParam, void, Machine
from .machine import this_machine_hash, machine_info
from .db_functions import reset_db

