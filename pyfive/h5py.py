### This file contains H5Py classes which are not used by
### pyfive, but which are included in the public API for
### htnetcdf which expects to see these H5PY classes.


from pyfive.datatype_msg import DatatypeMessage
from pyfive.h5t import TypeEnumID

import numpy as np
from pathlib import PurePosixPath

class Datatype:
    """ 
    Provides a minimal instantiation of an h5py DataType 
    suitable for use with enumerations.
    """
    def __init__(self, name, hfile, raw_dtype):
        self.id = TypeEnumID(raw_dtype)
        path = PurePosixPath(name)
        self.name = path.name
        self.parent = str(path.parent) if str(path.parent) != '' else '/'
        self.file = hfile
    @property
    def dtype(self):
        return self.id.dtype
    def __str__(self):
        return f'<HDF5 named type "{self.name}" (dtype {self.id.kind})>'
    
    

class Empty:

    """
    Proxy object to represent empty/null dataspaces (a.k.a H5S_NULL).
    This can have an associated dtype, but has no shape or data. This is not
    the same as an array with shape (0,). This class provided for compatibility
    with the H5Py API to support h5netcdf. In pyfive this is used to wrap
    attributes associated with null dataspaces.
    """
    shape = None
    size = None

    def __init__(self, dtype):
        self.dtype = np.dtype(dtype)

    def __eq__(self, other):
        if isinstance(other, Empty) and self.dtype == other.dtype:
            return True
        return False

    def __repr__(self):
        return "Empty(dtype={0!r})".format(self.dtype)