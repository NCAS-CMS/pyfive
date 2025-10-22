#
#  The support for h5t in pyfive is very minimal and may
#  not fully reflect the h5py.h5t behaviour as pyfive
#  only commits to the high level API and the minimal
#  underlying capability. 
#
from collections import namedtuple
import numpy as np

string_info = namedtuple('string_info', ['encoding', 'length'])
# ref_dtype = np.dtype("O")
# complex_dtype_map = {
#                 '>f4': '>c8',
#                 '<f4': '<c8',
#                 '>f8': '>c16',
#                 '<f8': '<c16',
#                }
#
#
#
# from dataclasses import dataclass, field
# from typing import Optional, Dict, Tuple, Union, List
#
# class P5Type:
#     """Base class for H5 types within pyfive."""
#     is_atomic: bool = True
#     type_id: Optional[int] = None
#
#     def __init__(self, dtype: Optional[Union[str, np.dtype]] = None):
#         self._dtype: Optional[np.dtype] = np.dtype(dtype) if dtype is not None else None
#
#     @property
#     def dtype(self) -> np.dtype:
#         """Return NumPy dtype."""
#         if self._dtype is None:
#             self._dtype = self._build_dtype()
#         return self._dtype
#
#     def _build_dtype(self) -> np.dtype:
#         """Subclasses implement this if dtype not provided at init."""
#         raise NotImplementedError
#
#
# class P5IntegerType(P5Type):
#     type_id = 0
#     def __init__(self, dtype: Union[str, np.dtype]):
#         super().__init__(dtype=np.dtype(dtype))
#
#
# class P5FloatType(P5Type):
#     type_id = 1
#     def __init__(self, dtype: Union[str, np.dtype]):
#         super().__init__(dtype=np.dtype(dtype))
#
#
# class P5ReferenceType(P5Type):
#     type_id = 7
#     def __init__(self, size: int, storage_dtype: Union[str, np.dtype]):
#         super().__init__()
#         self.size = size
#         self.storage_dtype = np.dtype(storage_dtype)
#         self.ref_dtype = np.dtype("<u8")
#         self.is_atomic = False
#
#     def _build_dtype(self) -> np.dtype:
#         return np.dtype(self.storage_dtype, metadata={"h5py_class": "REFERENCE"})
#
#
# class P5EnumType(P5Type):
#     type_id = 8
#     def __init__(self, base_dtype: Union[str, np.dtype], mapping: dict):
#         super().__init__()
#         self.base_dtype = np.dtype(base_dtype)
#         self.mapping = mapping
#         self.is_atomic = True
#
#     def _build_dtype(self) -> np.dtype:
#         return np.dtype(self.base_dtype, metadata={'enum': self.mapping})
#
#
# class P5OpaqueType(P5Type):
#     type_id = 5
#     def __init__(self, dtype_spec: str, size: int):
#         super().__init__()
#         self.dtype_spec = dtype_spec
#         self.size = size
#
#     def _build_dtype(self) -> np.dtype:
#         if self.dtype_spec.startswith('NUMPY:'):
#             dtype = np.dtype(self.dtype_spec[6:], metadata={'h5py_opaque': True})
#         else:
#             dtype = np.dtype(f'V{self.size}', metadata={'h5py_opaque': True})
#         return dtype
#
#
# class P5SequenceType(P5Type):
#     type_id = 9
#     def __init__(self, base_dtype: P5Type):
#         super().__init__()
#         self.base_dtype = base_dtype
#         self.is_atomic = False
#
#     def _build_dtype(self) -> np.dtype:
#         return np.dtype('O', metadata={'vlen': self.base_dtype.dtype})
#
#
# class H5StringType(P5Type):
#     type_id = 3
#     CHARACTER_SETS = {
#         0: "ASCII",
#         1: "UTF-8",
#     }
#
#     def __init__(self, character_set: int = 0):
#         super().__init__()
#         self.character_set = character_set
#         self.is_atomic = True
#
#     @property
#     def encoding(self) -> str:
#         return self.CHARACTER_SETS.get(self.character_set, "UNKNOWN")
#
#
# class H5FixedStringType(H5StringType):
#     def __init__(
#         self,
#         fixed_size: int,
#         padding: Optional[np.uint8] = None,
#         character_set: int = 0,
#         null_terminated: bool = False,
#     ):
#         super().__init__(character_set)
#         self.fixed_size = fixed_size
#         self.padding = padding
#         self.null_terminated = null_terminated
#
#     def _build_dtype(self) -> np.dtype:
#         if self.character_set == 0:  # ASCII
#             base_dtype = np.dtype(f'S{self.fixed_size}')
#         elif self.character_set == 1:  # UTF-8
#             base_dtype = np.dtype(f'<U{self.fixed_size}')
#         else:
#             raise ValueError(f"Unknown character_set: {self.character_set}")
#
#         return np.dtype(base_dtype, metadata={'h5py_encoding': self.encoding.lower()})
#
#
# class H5VlenStringType(H5StringType):
#     type_id = 9
#     def __init__(self, character_set: int = 1):
#         super().__init__(character_set)
#
#     def _build_dtype(self) -> np.dtype:
#         return np.dtype('O', metadata={'vlen': str if self.character_set else bytes})
#
#
# @dataclass
# class H5CompoundField:
#     name: str
#     offset: int
#     subtype: P5Type
#
#     @property
#     def is_atomic(self) -> bool:
#         return self.subtype.is_atomic
#
#
# class P5CompoundType(P5Type):
#     type_id = 6
#     def __init__(self, fields: list[H5CompoundField], size: Optional[int] = None):
#         super().__init__()
#         self.fields = fields
#         self.size = size
#         self.is_atomic = all(f.is_atomic for f in self.fields)
#         self.is_complex = self._check_complex()
#         if self.is_complex:
#             # map complex type using first field dtype
#             self._dtype = np.dtype(complex_dtype_map[self.fields[0].subtype.dtype.str])
#
#     def _check_complex(self) -> bool:
#         if len(self.fields) != 2:
#             return False
#         if self.fields[0].name not in {"r", "real"}:
#             return False
#         if self.fields[1].name not in {"i", "imag"}:
#             return False
#         if self.fields[0].offset != 0:
#             return False
#         if self.size is None or self.fields[1].offset != self.size // 2:
#             return False
#         return True
#
#     def _build_dtype(self) -> np.dtype:
#         names = [f.name for f in self.fields]
#         formats = [f.subtype.dtype for f in self.fields]
#         offsets = [f.offset for f in self.fields]
#
#         return np.dtype({
#             'names': names,
#             'formats': formats,
#             'offsets': offsets,
#             'itemsize': self.size,
#         })


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
    if dt.metadata and 'h5py_opaque' in dt.metadata:
        return True
    return False 



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
    """
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
    #ref = dtype
    #    If the dtype represents an HDF5 reference type, returns the reference
    #    class (either Reference or RegionReference).  Returns None if the dtype
    #    does not represent an HDF5 reference type.
    #"""

    if len(kwds) != 1:
        raise TypeError("Exactly one keyword may be provided")

    name, dt = kwds.popitem()

    if name == 'vlen':
        return check_string_dtype(dt)
    elif name == 'enum':
        return check_enum_dtype(dt)
    elif name == 'opaque':
        return check_opaque_dtype(dt)
    elif name == 'ref':
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
        if self._dtype.kind in {'i', 'u', 'f'}:
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
            self.__reversed = {v: k for k, v in self.metadata['enum'].items()}
        return self.metadata['enum'][name]
        
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
