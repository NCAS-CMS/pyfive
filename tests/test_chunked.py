""" Test pyfive's abililty to read multidimensional datasets. """
import os

import h5py
import numpy as np
import pytest
from numpy.testing import assert_array_equal

import pyfive

DIRNAME = os.path.dirname(__file__)
DATASET_CHUNKED_HDF5_FILE = os.path.join(DIRNAME, "data", 'chunked.hdf5')
DATASET_BTREEV2_HDF5_FILE = os.path.join(DIRNAME, "data", "btreev2.hdf5")


@pytest.fixture(scope='module')
def data():
    return np.array(list(range(10_000)), dtype=np.int32).reshape((100, 100))


@pytest.fixture(scope='module')
def name(data):
    name = os.path.join(os.path.dirname(__file__), 'btreev2-generated.hdf5')

    with h5py.File(name, "w", libver="latest") as f:
        # type 10 record - chunked without filters
        f.create_dataset(
            "btreev2",
            data=data,
            chunks=(10, 10),
            maxshape=(None, None),
            dtype="int32")

        # type 11 record - chunked with filters
        f.create_dataset(
            "btreev2_filters",
            data=data,
            chunks=(10, 10),
            maxshape=(None, None),
            compression="gzip",
            compression_opts=1,
            fletcher32=True,
            dtype="int32")

    return name


def test_chunked_dataset():
    with pyfive.File(DATASET_CHUNKED_HDF5_FILE) as hfile:
        # check data
        dset1 = hfile['dataset1']
        assert_array_equal(dset1[:], np.arange(21 * 16).reshape((21, 16)))
        assert dset1.chunks == (2, 2)


def test_recognise_btree(name, data):
    """ 
    At this point we want to raise an error if we find a chunked variable
    with a b-tree v2 index, as we don't know how to read it ... yet.
    It seems that can only come with layoutclass = 4. 
    """
    with pytest.raises(RuntimeError):
        with pyfive.File(name) as hfile:
            dset1 = hfile['btreev2']
            print(dset1)
        


@pytest.mark.skip(reason="Not implemented yet, see https://github.com/NCAS-CMS/pyfive/issues/137")
def test_chunked_dataset_btreev2(name, data):
    with pyfive.File(name) as hfile:
        dset1 = hfile['btreev2']
        assert_array_equal(dset1[...], data)

    with pyfive.File(DATASET_BTREEV2_HDF5_FILE) as hfile:
        dset1 = hfile['btreev2']
        assert_array_equal(dset1[...], data)
