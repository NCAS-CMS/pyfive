### This file contains H5Py classes which are not used by
### pyfive, but which are included in the public API for
### htnetcdf which expects to see these H5PY classes.


from pyfive.datatype_msg import DatatypeMessage
from pyfive.h5t import TypeNumID

import numpy as np

class Datatype:
    """ 
    Provides a minimal instantiation of a DataType suitable for use with
    enumerations.
    #FIXME: Should refactor to use this everywhere we use dtype
    """
    def __init__(self,*args,**kw):
        self.id = TypeNumID()
        #FIXME:ENUM
        raise NotImplementedError

class Empty:

    """
    Proxy object to represent empty/null dataspaces (a.k.a H5S_NULL).
    This can have an associated dtype, but has no shape or data. This is not
    the same as an array with shape (0,). This class provided for compatibility
    with the H5Py API to support h5netcdf. It is not used by pyfive.
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