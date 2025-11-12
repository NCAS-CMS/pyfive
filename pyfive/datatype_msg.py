""" Representation and reading of HDF5 datatype messages. """

from collections import OrderedDict

from .core import _padded_size, _structure_size, _unpack_struct_from
from .core import InvalidHDF5File

from .p5t import P5Type, P5CompoundType, P5CompoundField, P5FixedStringType, P5VlenStringType, P5SequenceType, P5EnumType, P5OpaqueType, P5FloatType, P5ReferenceType, P5StringType, P5IntegerType

import numpy as np


class DatatypeMessage(object):
    """ Representation of a HDF5 Datatype Message. """
    # Contents and layout defined in IV.A.2.d.

    def __init__(self, buf, offset):
        self.buf = buf
        self.offset = offset
        self.ptype = self.determine_dtype()

    def determine_dtype(self):
        """ Return the dtype (often numpy-like) for the datatype message.  """
        datatype_msg = _unpack_struct_from(DATATYPE_MSG, self.buf, self.offset)
        self.offset += DATATYPE_MSG_SIZE
        # last 4 bits
        datatype_class = datatype_msg['class_and_version'] & 0x0F

        if datatype_class == DATATYPE_FIXED_POINT:
            return self._determine_dtype_fixed_point(datatype_msg)
        elif datatype_class == DATATYPE_FLOATING_POINT:
            return self._determine_dtype_floating_point(datatype_msg)
        elif datatype_class == DATATYPE_TIME:
            raise NotImplementedError("Time datatype class not supported.")
        elif datatype_class == DATATYPE_STRING:
            return self._determine_dtype_string(datatype_msg)
        elif datatype_class == DATATYPE_BITFIELD:
            raise NotImplementedError("Bitfield datatype class not supported.")
        elif datatype_class == DATATYPE_OPAQUE:
            return self._determine_dtype_opaque(datatype_msg)
        elif datatype_class == DATATYPE_COMPOUND:
            return self._determine_dtype_compound(datatype_msg)
        elif datatype_class == DATATYPE_REFERENCE:
            return P5ReferenceType(datatype_msg['size'], f"V{datatype_msg['size']}")
        elif datatype_class == DATATYPE_ENUMERATED:
            return self._determine_dtype_enum(datatype_msg)
        elif datatype_class == DATATYPE_ARRAY:
            raise NotImplementedError("Array datatype class not supported.")
        elif datatype_class == DATATYPE_VARIABLE_LENGTH:
            return self._determine_dtype_vlen(datatype_msg)
        raise InvalidHDF5File('Invalid datatype class %i' % (datatype_class))

    def _determine_dtype_fixed_point(self, datatype_msg):
        """ Return the NumPy dtype for a fixed point class. """
        # fixed-point types are assumed to follow IEEE standard format
        length_in_bytes = datatype_msg['size']
        if length_in_bytes not in [1, 2, 4, 8]:
            raise NotImplementedError("Unsupported datatype size")

        signed = datatype_msg['class_bit_field_0'] & 0x08
        if signed > 0:
            dtype_char = 'i'
        else:
            dtype_char = 'u'

        byte_order = datatype_msg['class_bit_field_0'] & 0x01
        if byte_order == 0:
            byte_order_char = '<'  # little-endian
        else:
            byte_order_char = '>'  # big-endian

        # 4-byte fixed-point property description
        # not read, assumed to be IEEE standard format
        self.offset += 4

        return P5IntegerType(byte_order_char + dtype_char + str(length_in_bytes))

    def _determine_dtype_floating_point(self, datatype_msg):
        """ Return the NumPy dtype for a floating point class. """
        # Floating point types are assumed to follow IEEE standard formats
        length_in_bytes = datatype_msg['size']
        if length_in_bytes not in [1, 2, 4, 8]:
            raise NotImplementedError("Unsupported datatype size")

        dtype_char = 'f'

        byte_order = datatype_msg['class_bit_field_0'] & 0x01
        if byte_order == 0:
            byte_order_char = '<'  # little-endian
        else:
            byte_order_char = '>'  # big-endian

        # 12-bytes floating-point property description
        # not read, assumed to be IEEE standard format
        self.offset += 12

        return P5FloatType(byte_order_char + dtype_char + str(length_in_bytes))

    @staticmethod
    def _determine_dtype_string(datatype_msg):
        """ Return the NumPy dtype for a string class. """
        return P5FixedStringType(datatype_msg['size'])

    def _determine_dtype_compound(self, datatype_msg):
        """ Return the dtype of a compound class if supported. """
        bit_field_0 = datatype_msg['class_bit_field_0']
        bit_field_1 = datatype_msg['class_bit_field_1']
        n_comp = bit_field_0 + (bit_field_1 << 4)
        version = datatype_msg['class_and_version'] >> 4

        # read in the fields of the compound datatype
        # at the moment we need to skip two bytes which I do
        fields = []
        for _ in range(n_comp):
            null_location = self.buf.index(b'\x00', self.offset)
            # we read with padding and without
            name_size = null_location - self.offset + 1 if version == 3 else _padded_size(
                null_location - self.offset + 1, 8)
            name = self.buf[self.offset:self.offset+name_size]
            name = name.strip(b'\x00').decode('utf-8')
            self.offset += name_size

            # handle different message type versions
            if version == 1:
                prop_desc = _unpack_struct_from(
                    COMPOUND_PROP_DESC_V1, self.buf, self.offset)
                self.offset += COMPOUND_PROP_DESC_V1_SIZE
            elif version == 3:
                # according HDF5 manual
                # https://support.hdfgroup.org/documentation/hdf5/latest/_f_m_t4.html#subsec_fmt4_intro_doc
                offset_len = max(1, (datatype_msg["size"] - 1).bit_length() + 7 >> 3)
                fmt = {1: 'B', 2: 'H', 4: 'I', 8: 'Q'}[offset_len]
                offset_struct = OrderedDict((('offset', fmt),))
                prop_desc = _unpack_struct_from(offset_struct, self.buf, self.offset)
                self.offset += offset_len

            comp_dtype = self.determine_dtype()
            if not isinstance(comp_dtype, P5Type):
                raise TypeError(f"Field {name} is not an H5Type instance")
            fields.append(P5CompoundField(name=name, offset=prop_desc["offset"], ptype=comp_dtype))

        return P5CompoundType(fields=fields, size=datatype_msg["size"])


    def _determine_dtype_opaque(self, datatype_msg):
        """ Return the dtype information for an opaque class. """
        # Opaque types are not understood by pyfive, so we return
        # a tuple indicating the type is opaque, the size in bytes
        # and the tag, if any. The tag is an ascii string, null terminated 
        # and padded to an 8 byte boundary, the number of which is given by the 
        # message size.
        size =  datatype_msg['size']
        null_location = self.buf.index(b'\x00', self.offset)
        tag_size = _padded_size(null_location - self.offset + 1, 8)
        tag_bytes = self.buf[self.offset:self.offset+tag_size]
        tag = tag_bytes.strip(b'\x00').decode('ascii')
        self.offset += tag_size
        if tag == '':
            tag = None  
        
        return P5OpaqueType(tag, size)

    def _determine_dtype_vlen(self, datatype_msg):
        """ Return the dtype information for a variable length class. """
        vlen_type = datatype_msg['class_bit_field_0'] & 0x01
        if vlen_type != 1:
            return P5SequenceType(base_dtype=self.determine_dtype())
        character_set = datatype_msg['class_bit_field_1'] & 0x01
        return P5VlenStringType(character_set=character_set)

    def _determine_dtype_enum(self,datatype_msg):
        """ Return the basetype and the underlying enum dictionary """
        #FIXME: Consider overlap with the compound code, refactor in some way?
        # Doing this rather than what is done in compound data type as doing that is opaque and risky
        enum_msg = _unpack_struct_from(ENUM_DATATYPE_MSG, self.buf, self.offset-DATATYPE_MSG_SIZE)
        num_members = enum_msg['number_of_members']
        value_size = enum_msg['size']
        enum_keys = []
        dtype = DatatypeMessage(self.buf, self.offset).ptype.dtype
        self.offset+=12
        # An extra 4 bytes are read as part of establishing the data type
        # FIXME:ENUM Need to be sure that some other base type in the future
        # wouldn't silently need more bytes and screw this all up. Should 
        # probably put some check/error handling around this.
        # now get the keys
        version = (datatype_msg['class_and_version'] >> 4) & 0x0F
        for _ in range(num_members):
            null_location = self.buf.index(b'\x00', self.offset)
            name_size = null_location - self.offset + 1 if version == 3 else _padded_size(null_location - self.offset+ 1, 8)
            name = self.buf[self.offset:self.offset+name_size]
            name = name.strip(b'\x00').decode('ascii')
            self.offset += name_size
            enum_keys.append(name)
        #now get the values
        nbytes = value_size*num_members
        values = np.frombuffer(self.buf[self.offset:], dtype=dtype, count=num_members)
        enum_dict = {k:v for k,v in zip(enum_keys,values)}
        return P5EnumType(dtype, enum_dict)


# IV.A.2.d The Datatype Message

DATATYPE_MSG = OrderedDict((
    ('class_and_version', 'B'),
    ('class_bit_field_0', 'B'),
    ('class_bit_field_1', 'B'),
    ('class_bit_field_2', 'B'),
    ('size', 'I'),
))

DATATYPE_MSG_SIZE = _structure_size(DATATYPE_MSG)

ENUM_DATATYPE_MSG = OrderedDict((
    ('class_and_version', 'B'),
    ('number_of_members', 'H'),  # 'H' is a 16-bit unsigned integer
    ('unused', 'B'),
    ('size', 'I'),
))


COMPOUND_PROP_DESC_V1 = OrderedDict((
    ('offset', 'I'),
    ('dimensionality', 'B'),
    ('reserved_0', 'B'),
    ('reserved_1', 'B'),
    ('reserved_2', 'B'),
    ('permutation', 'I'),
    ('reserved_3', 'I'),
    ('dim_size_1', 'I'),
    ('dim_size_2', 'I'),
    ('dim_size_3', 'I'),
    ('dim_size_4', 'I'),
))
COMPOUND_PROP_DESC_V1_SIZE = _structure_size(COMPOUND_PROP_DESC_V1)


# Datatype message, datatype classes
DATATYPE_FIXED_POINT = 0
DATATYPE_FLOATING_POINT = 1
DATATYPE_TIME = 2
DATATYPE_STRING = 3
DATATYPE_BITFIELD = 4
DATATYPE_OPAQUE = 5
DATATYPE_COMPOUND = 6
DATATYPE_REFERENCE = 7
DATATYPE_ENUMERATED = 8
DATATYPE_VARIABLE_LENGTH = 9
DATATYPE_ARRAY = 10
