#
#  The support for h5t in pyfive is very minimal and may
#  not fully reflect the h5py.h5t behaviour as pyfive
#  only commits to the high level API and the minimal
#  underlying capability.
#
from collections import namedtuple

string_info = namedtuple("string_info", ["encoding", "length"])


def opaque_dtype(dt):
    """
    Return the numpy dtype of the dtype. (So it does nothing,
    but is included for compatibility with the h5py API
    docuemntation which _implies_ this is needed to read data,
    but it is not.)
    """
    # For pyfive, the opaque dtype is fully handled in h5d.py
    # and as this is really only for writing (where it marks
    # a dtype with metadata) we just return the dtype in
    # pyfive where we are only reading and users don't actually
    # need  this function. It is only included as the h5py docs
    # make it seem relevant for reading. It is not.
    return dt


def check_opaque_dtype(dt):
    """
    If the dtype represents an HDF5 opaque type, returns True.
    Returns False if the dtype does not represent an HDF5 opaque type.
    """
    if dt.metadata and "h5py_opaque" in dt.metadata:
        return True
    return False


def check_enum_dtype(dt):
    """
    If the dtype represents an HDF5 enumerated type, returns the dictionary
    mapping string names to integer values.
    Returns None if the dtype does not represent an HDF5 enumerated type.
    """
    try:
        return dt.metadata.get("enum", None)
    except AttributeError:
        return None


def check_string_dtype(dt):
    """
    The returned string_info object holds the encoding and the length.
    The encoding can only be 'utf-8'. The length will be None for a
    variable-length string.
    Returns None if the dtype does not represent a pyfive string.
    """
    if dt.kind == "S":
        return string_info("utf-8", dt.itemsize)

    if dt.kind == "O":
        # vlen string
        enc = (dt.metadata or {}).get("h5py_encoding", "ascii")
        return string_info(enc, None)

    return None


def check_dtype(**kwds):
    """
    Check a dtype for h5py special type "hint" information.  Only one
    keyword may be given.

    vlen = dtype
        If the dtype represents an HDF5 vlen, returns the Python base class.
        Currently only built-in string vlens (str) are supported.  Returns
        None if the dtype does not represent an HDF5 vlen.

    enum = dtype
        If the dtype represents an HDF5 enumerated type, returns the dictionary
        mapping string names to integer values.  Returns None if the dtype does
        not represent an HDF5 enumerated type.

    opaque = dtype
        If the dtype represents an HDF5 opaque type, returns True.  Returns False if the
        dtype does not represent an HDF5 opaque type.

    """
    # ref = dtype
    #    If the dtype represents an HDF5 reference type, returns the reference
    #    class (either Reference or RegionReference).  Returns None if the dtype
    #    does not represent an HDF5 reference type.
    # """

    if len(kwds) != 1:
        raise TypeError("Exactly one keyword may be provided")

    name, dt = kwds.popitem()

    if name == "vlen":
        return check_string_dtype(dt)
    elif name == "enum":
        return check_enum_dtype(dt)
    elif name == "opaque":
        return check_opaque_dtype(dt)
    elif name == "ref":
        raise NotImplementedError
    else:
        return None


class TypeID:
    """
    Used by DataType to expose internal structure of a generic
    datatype. This is instantiated by pyfive using arcane
    hdf5 structure information, and should not normally be
    needed by any user code.
    """

    def __init__(self, raw_dtype):
        """
        Initialised with the raw_dtype read from the message.
        This is not the same init signature as h5py!
        """
        super().__init__()
        self._dtype = raw_dtype.dtype
        self._h5typeid = raw_dtype.type_id

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        return self.dtype == other.dtype

    @property
    def dtype(self):
        """
        The numpy dtype.
        """
        return self._dtype

    @property
    def kind(self):
        s = self._dtype.str
        if self._dtype.kind in {"i", "u", "f"}:
            s = s.replace("<", "|")
        return s

    def get_class(self):
        return self._h5typeid


class TypeEnumID(TypeID):
    """
    Used by DataType to expose internal structure of an enum
    datatype. This is instantiated by pyfive using arcane
    hdf5 structure information, and should not normally be
    needed by any user code.
    """

    def __init__(self, raw_dtype):
        """
        Initialised with the raw_dtype read from the message.
        This is not the same init signature as h5py!
        """
        super().__init__(raw_dtype)
        self.__reversed = None

    @property
    def metadata(self):
        return self.dtype.metadata

    def enum_valueof(self, name):
        """
        Get the value associated with an enum name.
        """
        if self.__reversed == None:
            # cache for later
            self.__reversed = {v: k for k, v in self.metadata["enum"].items()}
        return self.metadata["enum"][name]

    def enum_nameof(self, index):
        """
        Determine the name associated with the given value.
        """
        return self.__reversed[index]

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        return self.metadata == other.metadata


class TypeCompoundID(TypeID):
    """
    Used by DataType to expose internal structure of a compound
    datatype.
    """

    pass
