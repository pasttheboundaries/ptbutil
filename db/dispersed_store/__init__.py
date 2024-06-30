"""
dispersed_store stands for dispersed domained store
The idea is to store data in a dispersed existing_files.
The names of the existing_files are constructed based on 2 features:
 - domain
 - data name index

The domain is a descriptor derived from the stored data.
Store instance when createxd needs to have domain_extraction declared which is expected to be a callable
that will return a domain name when called with the data to be saved.

The data name index is a number indexing a subsequent data names.
Creating subsequent data depends on a max_file_size parameter.
When the stored data exceds the parameter at data appending, a next data will be cxreated
and data name index will be increased by 1
like in file_1.csv, file_2.csv
Most recent dile has the biggest number.

"""
from .store import (DispersedSerialStore, SerialDomainStore, SerialData,
                    DispersedIndexedStore, IndexedDomainStore, IndexedData)
from .errors import Unable, MaxSizeReached