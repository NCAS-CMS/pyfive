#
#  The support for h5t in pyfive is very minimal and may
#  not fully reflect the h5py.h5t behaviour as pyfive
#  only commits to the high level API and the minimal
#  underlying capability. 
#
from collections import namedtuple

string_info = namedtuple('string_info', ['encoding', 'length'])


def check_enum_dtype(dt):
    """
    If the dtype represents an HDF5 enumerated type, returns the dictionary
    mapping string names to integer values.
    Returns None if the dtype does not represent an HDF5 enumerated type.
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

    if name == 'vlen':
        return check_string_dtype(dt)
    elif name == 'enum':
        return check_enum_dtype(dt)
    elif name == 'ref':
        return NotImplementedError
    else:
        return None

class TypeID:
    """ 
    Minimal Mixin Class for the necessary TypdID signature. 
    """
    def dtype(self):
        raise NotImplementedError
    def equal(self, other):
        return self == other
    def __eq__(self, other):
        raise NotImplementedError

class TypeNumID(TypeID):
    """ 
    Used by DataType to expose internal structure of an enum 
    datatype.
    """
    def __init__(self, raw_dtype):
        """ 
        Initialised with the raw_dtype read from the message.
        This is not the same init signature as h5py!
        """
        super().__init__()
        enum, dtype, enumdict = raw_dtype
        self.metadata = {'enum':enumdict}
        self.__reversed = None
        self.kind = dtype.replace('<','|')
    def enum_valueof(self, name):
        """
        Get the value associated with an enum name.
        """
        if self._reversed == None:
            # cache for later
            self.__reversed = {v: k for k, v in self.metadata['enum'].items()}
        return self.__reversed[name]
    def get_member_value(self, index):
        """
        Determine the name associated with the given value.
        """
        return self.metadata['enum'][index]
    def __eq__(sel, other):
        if type(self) != type(other):
            return False
        return self.metadadta == other.metadata
    @property
    def dtype(self):
        return np.metadata(self.kind,metadata=self.metadata)
    
