import os

import numpy as np
import pytest
from numpy.testing import assert_array_equal

import pyfive
import h5py


def test_opaque_dataset_hdf5(name, opdata):

    # Verify that h5py can read this file before we do
    # our own test. If this fails, pyfive cannot be 
    # expected to get it right.

    with h5py.File(name, "r") as f:
        dset = f["opaque_datetimes"]
        assert_array_equal(dset[...], opdata.astype(h5py.opaque_dtype(opdata.dtype)))

    # Now see if pyfive can do the right thin
    with pyfive.File(name) as hfile:
        # check data
        dset = hfile["opaque_datetimes"]
        # pyfive should return the same raw bytes that h5py wrote
        # but in the instance that it is tagged with NUMPY, 
        # pyfive automatically fixes it, which it should be for this example.
        assert_array_equal(dset[...], opdata)



@pytest.fixture(scope='module')
def opdata():
    """Provide datetime64 array data."""
    return np.array(
        [
            np.datetime64("2019-09-22T17:38:30"),
            np.datetime64("2020-01-01T00:00:00"),
            np.datetime64("2025-10-04T12:00:00"),
        ]
    )


@pytest.fixture(scope='module')
def name(opdata):
    """Create an HDF5 file with datetime64 data stored as opaque."""
    name = os.path.join(os.path.dirname(__file__), "opaque_datetime.hdf5")

    # Convert dtype to an opaque version (as per h5py docs)
    # AFIK this just adds {'h5py_opaque': True} to the dtype metadata
    # without which h5py cannot write the data.
    opaque_data = opdata.astype(h5py.opaque_dtype(opdata.dtype))

    with h5py.File(name, "w") as f:
        f["opaque_datetimes"] = opaque_data

    return name
