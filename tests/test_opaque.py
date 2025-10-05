import os

import numpy as np
import pytest
from numpy.testing import assert_array_equal

import pyfive
import h5py


def test_opaque_dataset_hdf5(name, data):

    # Verify that h5py can read this file before we do
    # our own test. If this fails, pyfive cannot be 
    # expected to get it right.

    (ordinary_data, string_data, opdata) = data

    with h5py.File(name, "r") as f:
        dset = f["opaque_datetimes"]
        assert_array_equal(dset[...], opdata.astype(h5py.opaque_dtype(opdata.dtype)))

    # Now see if pyfive can do the right thing
    with pyfive.File(name) as hfile:
        # check data
        dset = hfile["opaque_datetimes"]
        # pyfive should return the same raw bytes that h5py wrote
        # but in the instance that it is tagged with NUMPY, 
        # pyfive automatically fixes it, which it should be for this example.
        assert_array_equal(dset[...], opdata)

        # make sure the other things are fine
        assert_array_equal(hfile['string_data'][...],string_data)
        assert_array_equal(hfile['ordinary_data'][...],ordinary_data)

        assert pyfive.check_opaque_dtype(dset.dtype) is True
        assert pyfive.check_enum_dtype(dset.dtype) is None
        assert pyfive.check_opaque_dtype(hfile['ordinary_data'].dtype) is False
        assert pyfive.check_dtype(opaque=hfile['ordinary_data'].dtype) is False
        assert pyfive.check_dtype(opaque=hfile['opaque_datetimes'].dtype) is True






@pytest.fixture(scope='module')
def data():
    """Provide datetime64 array data."""
    ordinary_data = np.array([1, 2, 3], dtype='i4')
    string_data = np.array([b'one', b'two', b'three'], dtype='S5')
    opaque_data =  np.array([
            np.datetime64("2019-09-22T17:38:30"),
            np.datetime64("2020-01-01T00:00:00"),
            np.datetime64("2025-10-04T12:00:00"),
        ])

    data = (ordinary_data, string_data, opaque_data)
    
    return data


@pytest.fixture(scope='module')
def name(data):
    """Create an HDF5 file with datetime64 data stored as opaque."""
    name = os.path.join(os.path.dirname(__file__), "opaque_datetime.hdf5")

    (ordinary_data, string_data, opdata) = data

    # Convert dtype to an opaque version (as per h5py docs)
    # AFIK this just adds {'h5py_opaque': True} to the dtype metadata
    # without which h5py cannot write the data.

    opaque_data = opdata.astype(h5py.opaque_dtype(opdata.dtype))
   
    # Want to put some other things in the file too, so we can exercise
    # some of the other code paths.
   
    with h5py.File(name, "w") as f:
        f["opaque_datetimes"] = opaque_data
        f['string_data'] = string_data
        f['ordinary_data'] = ordinary_data

    return name
