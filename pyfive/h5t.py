#
# These are provided to support h5netcdf, and are not used
# by the pyfive package itself. 
# FIXME:ENUM
from collections import namedtuple


string_info = namedtuple('string_info', ['encoding', 'length'])


def check_enum_dtype(dt):
    """
    If the dtype represents an HDF5 enumerated type, returns the dictionary
    mapping string names to integer values.
    Returns None if the dtype does not represent an HDF5 enumerated type.
    ---
    Note that currently pyfive does not support HDF5 enumerated types,
    so this will always return None (see datatype_msg), and AFIK, should
    never get called in anger. It is only included so h5netcdf wont
    barf at its absence when pyfive is used as a backend.
    #FIXME:ENUM
    """
    try:
        return dt.metadata.get('enum', None)
    except AttributeError:
        return None
    
def check_string_dtype(dt):
    """Pyfive version of h5py.h5t.check_string_dtype.

    The returned string_info object holds the encoding and the length.
    The encoding can only be 'utf-8'. The length will be None for a
    variable-length string.

    Returns None if the dtype does not represent a pyfive string.
    """
    if dt.kind == 'S':
        return string_info('utf-8', dt.itemsize)

    if dt.kind == 'O':
        # vlen string
        enc = (dt.metadata or {}).get('h5py_encoding', 'ascii')
        return string_info(enc, None)

    return None

def check_dtype(**kwds):
    """ Check a dtype for h5py special type "hint" information.  Only one
    keyword may be given.

    vlen = dtype
        If the dtype represents an HDF5 vlen, returns the Python base class.
        Currently only built-in string vlens (str) are supported.  Returns
        None if the dtype does not represent an HDF5 vlen.

    enum = dtype
        If the dtype represents an HDF5 enumerated type, returns the dictionary
        mapping string names to integer values.  Returns None if the dtype does
        not represent an HDF5 enumerated type.

    ref = dtype
        If the dtype represents an HDF5 reference type, returns the reference
        class (either Reference or RegionReference).  Returns None if the dtype
        does not represent an HDF5 reference type.
    """

    if len(kwds) != 1:
        raise TypeError("Exactly one keyword may be provided")

    name, dt = kwds.popitem()

    if name not in ('vlen', 'enum', 'ref'):
        raise TypeError('Unknown special type "%s"' % name)

    try:
        return dt.metadata[name]
    except TypeError:
        return None
    except KeyError:
        return None


class TypeNumID:
    """ 
    Used by DataType to expose internal structure.
    It is not obvious pyfive needs an implementation of this.
    #FIXME:ENUM consider whether we should use this where we have enum dicts. What does H5py do?
    # This is low level so we don't have to follow their API this deep, but is there an advantage
    # in doing so? We could implement this using a souped up dictionary and not call it the same thing.
    """
    def __init__(self,*args,**kw):
        pass
    def __str__(self):
        return 'Not implemented'
