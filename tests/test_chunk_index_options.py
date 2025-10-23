""" Test pyfive's abililty to read multidimensional datasets. """
import os

import numpy as np
from numpy.testing import assert_array_equal

import pyfive

DIRNAME = os.path.dirname(__file__)
DATASET_CHUNKED_HDF5_FILE = os.path.join(DIRNAME, "data", 'chunked.hdf5')


def test_lazy_index():

    with pyfive.File(DATASET_CHUNKED_HDF5_FILE) as hfile:

        # instantiate variable
        dset1 = hfile.get_lazy_view('dataset1')

        # should be able to see attributes but not have an index yet
        assert dset1.attrs['attr1'] == 130

        # test we have no index yet 
        assert dset1.id._DatasetID__index_built==False

        # this should force an index build
        assert_array_equal(dset1[:], np.arange(21*16).reshape((21, 16)))
        assert dset1.chunks == (2, 2)