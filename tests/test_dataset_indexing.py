""" Test pyfive's abililty to index Datasets. """
import os

import numpy as np
from numpy.testing import assert_array_equal

import pyfive

DIRNAME = os.path.dirname(__file__)
DATASET_MULTIDIM_HDF5_FILE = os.path.join(DIRNAME, 'data/dataset_multidim.hdf5')


def test_dataset_indexing():

    with pyfive.File(DATASET_MULTIDIM_HDF5_FILE) as hfile:

        # check shape
        assert hfile['d'][:].shape == (2, 3, 4, 5)

        d = hfile['d']  # pyfive Dataset
        array = d[...]  # numpy array 

        # Check one dimension at a time with a -ve step slice
        index0 = [slice(None)] * d.ndim
        for i in range(len(index0)):
            index = index0[:]
            index[i] = slice(None, None, -1)            
            assert_array_equal(d[tuple(index)], array[tuple(index)])

        # Check 1, 2, ... dimensions with -ve step slices (overwriting
        # index0)
        for i in range(len(index0)):
            index0[i] = slice(None, None, -1)
            assert_array_equal(d[tuple(index0)], array[tuple(index0)])

        # Check one scalar index with two list indices
        index0 = [0] * d.ndim
        index0[2] = [1, 2]
        index0[3] = [1, 4]
        for i in (0, 1):
            index[i] = i
            assert_array_equal(d[tuple(index)], array[tuple(index)])

        # Check multiple scalar index multiple scalar index with two
        # list indices
        for i in  (0, 1):
            index0[i] = 0
            assert_array_equal(d[tuple(index0)], array[tuple(index0)])

        # Check all everything at once
        index0 = [slice(None,), 0, [1, 2], slice(5, None, -2)]
        assert_array_equal(d[tuple(index0)], array[tuple(index0)])
