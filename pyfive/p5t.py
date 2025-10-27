
import numpy as np
from dataclasses import dataclass

ref_dtype = np.dtype("O")
complex_dtype_map = {
                '>f4': '>c8',
                '<f4': '<c8',
                '>f8': '>c16',
                '<f8': '<c16',
               }

class P5Type:
    """Base class for P5 types within pyfive."""
    is_atomic = True
    type_id = None

    def __init__(self, dtype = None):
        self._dtype = np.dtype(dtype) if dtype is not None else None

    @property
    def dtype(self):
        """Return NumPy dtype."""
        if self._dtype is None:
            self._dtype = self._build_dtype()
        return self._dtype

    def _build_dtype(self):
        """Subclasses implement this if dtype not provided at init."""
        raise NotImplementedError


class P5IntegerType(P5Type):
    type_id = 0
    def __init__(self, dtype):
        super().__init__(dtype=np.dtype(dtype))


class P5FloatType(P5Type):
    type_id = 1
    def __init__(self, dtype):
        super().__init__(dtype=np.dtype(dtype))


class P5ReferenceType(P5Type):
    type_id = 7
    def __init__(self, size, storage_dtype):
        super().__init__()
        self.size = size
        self.storage_dtype = np.dtype(storage_dtype)
        self.ref_dtype = np.dtype("<u8")
        self.is_atomic = False

    def _build_dtype(self):
        return np.dtype(self.storage_dtype, metadata={"h5py_class": "REFERENCE"})


class P5EnumType(P5Type):
    type_id = 8
    def __init__(self, base_dtype, mapping):
        super().__init__()
        self.base_dtype = np.dtype(base_dtype)
        self.mapping = mapping
        self.is_atomic = True

    def _build_dtype(self):
        return np.dtype(self.base_dtype, metadata={'enum': self.mapping})


class P5OpaqueType(P5Type):
    type_id = 5
    def __init__(self, dtype_spec: str, size: int):
        super().__init__()
        self.dtype_spec = dtype_spec
        self.size = size

    def _build_dtype(self):
        if self.dtype_spec.startswith('NUMPY:'):
            dtype = np.dtype(self.dtype_spec[6:], metadata={'h5py_opaque': True})
        else:
            dtype = np.dtype(f'V{self.size}', metadata={'h5py_opaque': True})
        return dtype


class P5SequenceType(P5Type):
    type_id = 9
    def __init__(self, base_dtype):
        super().__init__()
        self.base_dtype = base_dtype
        self.is_atomic = False

    def _build_dtype(self):
        return np.dtype('O', metadata={'vlen': self.base_dtype.dtype})


class P5StringType(P5Type):
    type_id = 3
    CHARACTER_SETS = {
        0: "ASCII",
        1: "UTF-8",
    }

    def __init__(self, character_set):
        super().__init__()
        self.character_set = character_set
        self.is_atomic = True

    @property
    def encoding(self):
        return self.CHARACTER_SETS.get(self.character_set, "UNKNOWN")


class P5FixedStringType(P5StringType):
    def __init__(
        self,
        fixed_size,
        padding = None,
        character_set = 0,
        null_terminated = False,
    ):
        super().__init__(character_set)
        self.fixed_size = fixed_size
        self.padding = padding
        self.null_terminated = null_terminated

    def _build_dtype(self):
        if self.character_set == 0:  # ASCII
            base_dtype = np.dtype(f'S{self.fixed_size}')
        elif self.character_set == 1:  # UTF-8
            base_dtype = np.dtype(f'<U{self.fixed_size}')
        else:
            raise ValueError(f"Unknown character_set: {self.character_set}")

        return np.dtype(base_dtype, metadata={'h5py_encoding': self.encoding.lower()})


class P5VlenStringType(P5StringType):
    type_id = 9
    def __init__(self, character_set = 1):
        super().__init__(character_set)

    def _build_dtype(self):
        return np.dtype('O', metadata={'vlen': str if self.character_set else bytes})


@dataclass
class P5CompoundField:
    name: str
    offset: int
    ptype: P5Type

    @property
    def is_atomic(self):
        return self.ptype.is_atomic


class P5CompoundType(P5Type):
    type_id = 6
    def __init__(self, fields, size=None):
        super().__init__()
        self.fields = fields
        self.size = size
        self.is_atomic = all(f.is_atomic for f in self.fields)
        self.is_complex = self._check_complex()
        if self.is_complex:
            # map complex type using first field dtype
            self._dtype = np.dtype(complex_dtype_map[self.fields[0].ptype.dtype.str])

    def _check_complex(self):
        if len(self.fields) != 2:
            return False
        if self.fields[0].name not in {"r", "real"}:
            return False
        if self.fields[1].name not in {"i", "imag"}:
            return False
        if self.fields[0].offset != 0:
            return False
        if self.size is None or self.fields[1].offset != self.size // 2:
            return False
        return True

    def _build_dtype(self):
        names = [f.name for f in self.fields]
        formats = [f.ptype.dtype for f in self.fields]
        offsets = [f.offset for f in self.fields]

        return np.dtype({
            'names': names,
            'formats': formats,
            'offsets': offsets,
            'itemsize': self.size,
        })
