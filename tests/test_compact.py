import os

import numpy as np
from numpy.testing import assert_array_equal

import pyfive

DIRNAME = os.path.dirname(__file__)
DATASET_CHUNKED_HDF5_FILE = os.path.join(DIRNAME, 'compact.hdf5')


def test_chunked_dataset():

    with pyfive.File(DATASET_CHUNKED_HDF5_FILE) as hfile:
        data = np.array([1, 2, 3, 4], dtype=np.int32)

        # check data
        dset1 = hfile['compact']
        assert_array_equal(dset1[...], data)
