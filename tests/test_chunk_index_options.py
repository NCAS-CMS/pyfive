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


def test_lazy_visititems():

    def simpler_check(x,y):
        """ Expect this to be visited and instantiated without an index """
        print(x,y.name)
        assert y.attrs['attr1'] == 130
        assert y.id._DatasetID__index_built==False

    def simplest_check(x,y):
        """ Expect this to be visited and instantiated with an index """
        print(x,y.name)
        assert y.attrs['attr1'] == 130
        assert y.id._DatasetID__index_built==True

   
    with pyfive.File(DATASET_CHUNKED_HDF5_FILE) as hfile:

        assert hfile.visititems(simpler_check,noindex=True) is None
        assert hfile.visititems(simplest_check) is None






