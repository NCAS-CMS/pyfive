""" Unit tests for pyfive. """
import os
import sys
import subprocess

import numpy as np
from numpy.testing import assert_array_equal
import pytest

import pyfive

DIRNAME = os.path.dirname(__file__)
ATTR_DATATYPES_HDF5_FILE = os.path.join(DIRNAME, 'attr_datatypes.hdf5')
MAKE_ATTR_DATATYPES_SCRIPT = os.path.join(DIRNAME, 'make_attr_datatypes_file.py')
ATTR_DATATYPES_HDF5_FILE_2 = os.path.join(DIRNAME, 'attr_datatypes_2.hdf5')


@pytest.fixture(scope="module")
def attr_datatypes_hdf5(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("attr_datatypes")
    path = tmp_dir / "attr_datatypes.hdf5"
    subprocess.run([sys.executable, MAKE_ATTR_DATATYPES_SCRIPT, str(path)], check=True)
    return str(path)


def test_numeric_scalar_attr_datatypes():

    with pyfive.File(ATTR_DATATYPES_HDF5_FILE) as hfile:

        assert hfile.attrs['int08_little'] == -123
        assert hfile.attrs['int16_little'] == -123
        assert hfile.attrs['int32_little'] == -123
        assert hfile.attrs['int64_little'] == -123

        # These are 2**(size_in_bytes-1)+2 which could not be stored in
        # signed type of the same size
        assert hfile.attrs['uint08_little'] == 130
        assert hfile.attrs['uint16_little'] == 32770
        assert hfile.attrs['uint32_little'] == 2147483650
        assert hfile.attrs['uint64_little'] == 9223372036854775810

        assert hfile.attrs['int08_big'] == -123
        assert hfile.attrs['int16_big'] == -123
        assert hfile.attrs['int32_big'] == -123
        assert hfile.attrs['int64_big'] == -123

        assert hfile.attrs['uint08_big'] == 130
        assert hfile.attrs['uint16_big'] == 32770
        assert hfile.attrs['uint32_big'] == 2147483650
        assert hfile.attrs['uint64_big'] == 9223372036854775810

        assert hfile.attrs['float32_little'] == 123.
        assert hfile.attrs['float64_little'] == 123.

        assert hfile.attrs['float32_big'] == 123.
        assert hfile.attrs['float64_big'] == 123.


def test_complex_scalar_attr_datatypes():

    with pyfive.File(ATTR_DATATYPES_HDF5_FILE) as hfile:

        assert hfile.attrs['complex64_little'] == (123 + 456j)
        assert hfile.attrs['complex128_little'] == (123 + 456j)

        assert hfile.attrs['complex64_big'] == (123 + 456j)
        assert hfile.attrs['complex128_big'] == (123 + 456j)


def test_string_scalar_attr_datatypes():

    with pyfive.File(ATTR_DATATYPES_HDF5_FILE) as hfile:

        assert hfile.attrs['string_one'] == b'H'
        assert hfile.attrs['string_two'] == b'Hi'

        assert hfile.attrs['vlen_string'] == 'Hello'
        assert hfile.attrs['vlen_unicode'] == (
            u'Hello' + b'\xc2\xa7'.decode('utf-8'))


def test_numeric_array_attr_datatypes():

    with pyfive.File(ATTR_DATATYPES_HDF5_FILE) as hfile:

        assert_array_equal(hfile.attrs['int32_array'], [-123, 45])
        assert_array_equal(hfile.attrs['uint64_array'], [12, 34])
        assert_array_equal(hfile.attrs['float32_array'], [123, 456])

        assert hfile.attrs['int32_array'].dtype == np.dtype('<i4')
        assert hfile.attrs['uint64_array'].dtype == np.dtype('>u8')
        assert hfile.attrs['float32_array'].dtype == np.dtype('<f4')

        assert hfile.attrs['vlen_str_array'][0] == b'Hello'
        assert hfile.attrs['vlen_str_array'][1] == b'World!'

        assert hfile.attrs['vlen_str_array'].dtype == np.dtype('S6')


def test_string_array_attr_datatypes(attr_datatypes_hdf5):

    with pyfive.File(attr_datatypes_hdf5) as hfile:

        # bytes
        assert hfile.attrs['vlen_str_array'][0] == b'Hello'
        assert hfile.attrs['vlen_str_array'][1] == b'World!'

        assert hfile.attrs['vlen_str_array'].dtype == np.dtype('S6')

        # strings
        assert hfile.attrs['vlen_str_array1'][0] == 'Hello'
        assert hfile.attrs['vlen_str_array1'][1] == 'World!'

        assert hfile.attrs['vlen_str_array1'].dtype == np.dtype('O')
        assert hfile.attrs['vlen_str_array1'].dtype.metadata == {'h5py_encoding': 'utf-8'}


def test_vlen_sequence_attr_datatypes():

    with pyfive.File(ATTR_DATATYPES_HDF5_FILE) as hfile:

        vlen_attr = hfile.attrs['vlen_int32']
        assert len(vlen_attr) == 2
        assert_array_equal(vlen_attr[0], [-1, 2])
        assert_array_equal(vlen_attr[1], [3, 4, 5])

        vlen_attr = hfile.attrs['vlen_uint64']
        assert len(vlen_attr) == 3
        assert_array_equal(vlen_attr[0], [1, 2])
        assert_array_equal(vlen_attr[1], [3, 4, 5])
        assert_array_equal(vlen_attr[2], [42])

        vlen_attr = hfile.attrs['vlen_float32']
        assert len(vlen_attr) == 3
        assert_array_equal(vlen_attr[0], [0])
        assert_array_equal(vlen_attr[1], [1, 2, 3])
        assert_array_equal(vlen_attr[2], [4, 5])


def test_enum_attr_datatypes(attr_datatypes_hdf5):

    with pyfive.File(attr_datatypes_hdf5) as hfile:
        import h5py
        enum_attr = hfile.attrs['enum']
        assert enum_attr == 2
        assert enum_attr.dtype == h5py.special_dtype(
            enum=(np.int32, {'one': 1, 'two': 2, 'three': 3})
        )


def test_empty_string_datatypes(attr_datatypes_hdf5):

    with pyfive.File(attr_datatypes_hdf5) as hfile:
        enum_attr = hfile.attrs['empty_string']
        assert enum_attr == pyfive.Empty(dtype=np.dtype('|S1'))
        assert enum_attr.dtype == np.dtype('|S1')


def test_attributes_2():

    ascii = "ascii"
    unicode = "unicodé"

    with pyfive.File(ATTR_DATATYPES_HDF5_FILE_2) as ds:
        foobar = "foobár"
        assert isinstance(ds.attrs["unicode"], str)
        assert ds.attrs["unicode"] == unicode
        assert isinstance(ds.attrs["unicode_0dim"], str)
        assert ds.attrs["unicode_0dim"] == unicode
        assert isinstance(ds.attrs["unicode_1dim"], np.ndarray)
        assert ds.attrs["unicode_1dim"] == unicode
        assert isinstance(ds.attrs["unicode_arrary"], np.ndarray)
        assert (ds.attrs["unicode_arrary"] == [unicode, "foobár"]).all()
        assert isinstance(ds.attrs["unicode_list"], np.ndarray)
        assert (ds.attrs["unicode_list"] == unicode).all()

        # bytes and strings are received as strings for h5py3
        foobar = "foobar"
        assert isinstance(ds.attrs["ascii"], str)
        assert ds.attrs["ascii"] == "ascii"
        assert isinstance(ds.attrs["ascii_0dim"], str)
        assert ds.attrs["ascii_0dim"] == ascii
        assert isinstance(ds.attrs["ascii_1dim"], np.ndarray)
        assert ds.attrs["ascii_1dim"] == ascii
        assert isinstance(ds.attrs["ascii_array"], np.ndarray)
        assert (ds.attrs["ascii_array"] == [ascii, foobar]).all()
        assert isinstance(ds.attrs["ascii_list"], np.ndarray)
        assert ds.attrs["ascii_list"] == "ascii"

        assert isinstance(ds.attrs["bytes"], str)
        assert ds.attrs["bytes"] == ascii
        assert isinstance(ds.attrs["bytes_0dim"], str)
        assert ds.attrs["bytes_0dim"] == ascii
        assert isinstance(ds.attrs["bytes_1dim"], np.ndarray)
        assert ds.attrs["bytes_1dim"] == ascii
        assert isinstance(ds.attrs["bytes_array"], np.ndarray)
        assert (ds.attrs["bytes_array"] == [ascii, foobar]).all()
        assert isinstance(ds.attrs["bytes_list"], np.ndarray)
        assert ds.attrs["bytes_list"] == "ascii"

        foobar = "foobár"
        assert isinstance(ds.attrs["unicode_fixed"], np.bytes_)
        assert ds.attrs["unicode_fixed"] == np.array(unicode.encode())
        assert isinstance(ds.attrs["unicode_fixed_0dim"], np.bytes_)
        assert ds.attrs["unicode_fixed_0dim"] == np.array(unicode.encode())
        assert isinstance(ds.attrs["unicode_fixed_1dim"], np.ndarray)
        assert ds.attrs["unicode_fixed_1dim"] == np.array(unicode.encode())
        assert isinstance(ds.attrs["unicode_fixed_arrary"], np.ndarray)
        assert (ds.attrs["unicode_fixed_arrary"] == np.array(
            [unicode.encode(), foobar.encode()]
        )).all()

        foobar = "foobar"
        assert isinstance(ds.attrs["ascii_fixed"], np.bytes_)
        assert ds.attrs["ascii_fixed"] == np.array(ascii.encode())
        assert isinstance(ds.attrs["ascii_fixed_0dim"], np.bytes_)
        assert ds.attrs["ascii_fixed_0dim"] == np.array(ascii.encode())
        assert isinstance(ds.attrs["ascii_fixed_1dim"], np.ndarray)
        assert ds.attrs["ascii_fixed_1dim"] == np.array(ascii.encode())
        assert isinstance(ds.attrs["ascii_fixed_array"], np.ndarray)
        assert (ds.attrs["ascii_fixed_array"] == np.array([ascii.encode(), "foobar".encode()])).all()

        assert isinstance(ds.attrs["bytes_fixed"], np.bytes_)
        assert ds.attrs["bytes_fixed"] == np.array(ascii.encode())
        assert isinstance(ds.attrs["bytes_fixed_0dim"], np.bytes_)
        assert ds.attrs["bytes_fixed_0dim"] == np.array(ascii.encode())
        assert isinstance(ds.attrs["bytes_fixed_1dim"], np.ndarray)
        assert ds.attrs["bytes_fixed_1dim"] == np.array(ascii.encode())
        assert isinstance(ds.attrs["bytes_fixed_array"], np.ndarray)
        assert (ds.attrs["bytes_fixed_array"] == np.array([ascii.encode(), "foobar".encode()])).all()

        assert ds.attrs["int"] == 1
        assert ds.attrs["intlist"] == 1
        np.testing.assert_equal(ds.attrs["int_array"], np.arange(10))
        np.testing.assert_equal(ds.attrs["empty_list"], np.array([]))
        np.testing.assert_equal(ds.attrs["empty_array"], np.array([]))
