""" Unit tests for pyfive. """
import os
import sys
import subprocess

import numpy as np
from numpy.testing import assert_array_equal
import pytest

import pyfive

DIRNAME = os.path.dirname(__file__)
DATASET_DATATYPES_HDF5_FILE = os.path.join(DIRNAME, 'data', 'dataset_datatypes.hdf5')
MAKE_DATASET_DATATYPES_SCRIPT = os.path.join(DIRNAME, 'make_dataset_datatypes_file.py')


@pytest.fixture(scope="module")
def dataset_datatypes_hdf5(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("dataset_datatypes")
    path = tmp_dir / "dataset_datatypes.hdf5"
    subprocess.run([sys.executable, MAKE_DATASET_DATATYPES_SCRIPT, str(path)], check=True)
    return str(path)


def test_signed_int_dataset_datatypes():

    with pyfive.File(DATASET_DATATYPES_HDF5_FILE) as hfile:

        # check data
        ref_data = -np.arange(4)
        assert_array_equal(hfile['int08_little'][:], ref_data)
        assert_array_equal(hfile['int16_little'][:], ref_data)
        assert_array_equal(hfile['int32_little'][:], ref_data)
        assert_array_equal(hfile['int64_little'][:], ref_data)

        assert_array_equal(hfile['int08_big'][:], ref_data)
        assert_array_equal(hfile['int16_big'][:], ref_data)
        assert_array_equal(hfile['int32_big'][:], ref_data)
        assert_array_equal(hfile['int64_big'][:], ref_data)

        # check dtype
        assert hfile['int08_little'].dtype == np.dtype('<i1')
        assert hfile['int16_little'].dtype == np.dtype('<i2')
        assert hfile['int32_little'].dtype == np.dtype('<i4')
        assert hfile['int64_little'].dtype == np.dtype('<i8')

        assert hfile['int08_big'].dtype == np.dtype('>i1')
        assert hfile['int16_big'].dtype == np.dtype('>i2')
        assert hfile['int32_big'].dtype == np.dtype('>i4')
        assert hfile['int64_big'].dtype == np.dtype('>i8')


def test_signed_int_datatypes(dataset_datatypes_hdf5):

    with pyfive.File(dataset_datatypes_hdf5) as hfile:

        assert isinstance(hfile['int08_little_type'].id, pyfive.h5t.TypeID)
        assert hfile['int08_little_type'].id == hfile['int08_little_type2'].id
        assert hfile['int08_little_type'].id != hfile['complex64_little_type'].id


def test_unsigned_int_dataset_datatypes():

    with pyfive.File(DATASET_DATATYPES_HDF5_FILE) as hfile:

        # check data
        ref_data = np.arange(4)
        assert_array_equal(hfile['uint08_little'][:], ref_data)
        assert_array_equal(hfile['uint16_little'][:], ref_data)
        assert_array_equal(hfile['uint32_little'][:], ref_data)
        assert_array_equal(hfile['uint64_little'][:], ref_data)

        assert_array_equal(hfile['uint08_big'][:], ref_data)
        assert_array_equal(hfile['uint16_big'][:], ref_data)
        assert_array_equal(hfile['uint32_big'][:], ref_data)
        assert_array_equal(hfile['uint64_big'][:], ref_data)

        # check dtype
        assert hfile['uint08_little'].dtype == np.dtype('<u1')
        assert hfile['uint16_little'].dtype == np.dtype('<u2')
        assert hfile['uint32_little'].dtype == np.dtype('<u4')
        assert hfile['uint64_little'].dtype == np.dtype('<u8')

        assert hfile['uint08_big'].dtype == np.dtype('>u1')
        assert hfile['uint16_big'].dtype == np.dtype('>u2')
        assert hfile['uint32_big'].dtype == np.dtype('>u4')
        assert hfile['uint64_big'].dtype == np.dtype('>u8')


def test_float_dataset_datatypes():

    with pyfive.File(DATASET_DATATYPES_HDF5_FILE) as hfile:

        # check data
        ref_data = np.arange(4)
        assert_array_equal(hfile['float32_little'][:], ref_data)
        assert_array_equal(hfile['float64_little'][:], ref_data)

        assert_array_equal(hfile['float32_big'][:], ref_data)
        assert_array_equal(hfile['float64_big'][:], ref_data)

        # check dtype
        assert hfile['float32_little'].dtype == np.dtype('<f4')
        assert hfile['float64_little'].dtype == np.dtype('<f8')

        assert hfile['float32_big'].dtype == np.dtype('>f4')
        assert hfile['float64_big'].dtype == np.dtype('>f8')


def test_complex_dataset_datatypes(dataset_datatypes_hdf5):

    with pyfive.File(dataset_datatypes_hdf5) as hfile:
        ref_data = 123+456.j

        assert isinstance(hfile['complex64_little_type'].id, pyfive.h5t.TypeCompoundID)
        assert hfile['complex64_little_type'].id == hfile['complex64_little_type2'].id
        assert hfile['complex64_little_type'].id != hfile['int08_little_type'].id

        assert hfile["complex64_little_type"].dtype == np.dtype("<c8")
        assert hfile["complex64_big_type"].dtype == np.dtype(">c8")
        assert hfile["complex128_little_type"].dtype == np.dtype("<c16")
        assert hfile["complex128_big_type"].dtype == np.dtype(">c16")

        assert_array_equal(hfile['complex64_little'][:], ref_data)
        assert_array_equal(hfile['complex128_little'][:], ref_data)

        assert_array_equal(hfile['complex64_big'][:], ref_data)
        assert_array_equal(hfile['complex128_big'][:], ref_data)

        # check dtype
        assert hfile['complex64_little'].dtype == np.dtype('<c8')
        assert hfile['complex128_little'].dtype == np.dtype('<c16')

        assert hfile['complex64_big'].dtype == np.dtype('>c8')
        assert hfile['complex128_big'].dtype == np.dtype('>c16')


@pytest.mark.parametrize("base", ["i", "u", "f"])
@pytest.mark.parametrize("width", ["1", "2", "4", "8"])
@pytest.mark.parametrize("endian", ["<", ">"])
def test_vlen_dataset_datatypes(dataset_datatypes_hdf5, base, width, endian):
    if base == "f" and width == "1":
        pytest.skip("no 1 byte floats")
    tstr = "".join([endian, base, width])
    dtype = np.dtype(tstr)
    ref_data = np.empty(4, dtype=object)
    ref_data[0] = np.array([0], dtype)
    ref_data[1] = np.array([0, 1], dtype)
    ref_data[2] = np.array([0, 1, 2], dtype)
    ref_data[3] = np.array([0, 1, 2, 3], dtype)

    with pyfive.File(dataset_datatypes_hdf5) as hfile:

        assert hfile[f"vlen_{tstr}_type"].dtype == dtype
        assert isinstance(hfile[f"vlen_{tstr}_type"].id, pyfive.h5t.TypeID)

        # vlen sequence isn't implemented yet
        with pytest.raises(NotImplementedError, match="datatype not implemented - VLEN_SEQUENCE"):
            assert_array_equal(hfile[f"vlen_{tstr}"][:], ref_data)


