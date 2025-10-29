""" 
Test pyfive's abililty to read multidimensional datasets
and variants of the chunk index accesses 
"""
import os

import numpy as np
from numpy.testing import assert_array_equal

import pyfive
from pyfive.h5d import StoreInfo
import pytest
import h5py

DIRNAME = os.path.dirname(__file__)
DATASET_CHUNKED_HDF5_FILE = os.path.join(DIRNAME, "data", 'chunked.hdf5')

NOT_CHUNKED_FILE = os.path.join(DIRNAME, "data", 'issue23_A_contiguous.nc')


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


def test_get_chunk_info_chunked():

    # Start lazy, then go real
    # we think we know what the right answers are, so we hard
    # code them as well as check that's what h5py would return

      with pyfive.File(DATASET_CHUNKED_HDF5_FILE) as hfile, \
            h5py.File(DATASET_CHUNKED_HDF5_FILE) as h5f, \
            open(DATASET_CHUNKED_HDF5_FILE, "rb") as f:

        ds = hfile.get_lazy_view('dataset1')
        assert ds.id._DatasetID__index_built==False

        si = StoreInfo((0,0), 0, 4016, 16)
        info = ds.id.get_chunk_info(0)
        assert info == si
        assert h5f["dataset1"].id.get_chunk_info(0) == si

        assert ds.id.get_num_chunks() == 88
        assert h5f["dataset1"].id.get_num_chunks() == 88
    
        assert ds.id.btree_range == (1072, 8680)
        f.seek(1072)
        assert f.read(4) == b"TREE"  # only v1 btrees
        f.seek(8680)
        assert f.read(4) == b"TREE"  # only v1 btrees

    

def test_get_chunk_methods_contiguous():

    with pyfive.File(NOT_CHUNKED_FILE) as hfile:

        ds = hfile.get_lazy_view('q')
        assert ds.id._DatasetID__index_built==False

        with pytest.raises(TypeError):
            ds.id.get_chunk_info(0)

        with pytest.raises(TypeError):
            ds.id.get_num_chunks()

        with pytest.raises(TypeError):
            ds.id.read_direct_chunk(0)

        with pytest.raises(TypeError):
            ds.id.btree_range

        

        












