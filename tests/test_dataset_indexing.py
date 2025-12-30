""" Test pyfive's abililty to index Datasets."""
import os

import numpy as np
from numpy.testing import assert_array_equal
import pytest

import pyfive

DIRNAME = os.path.dirname(__file__)
DATASET_CONTIGUOUS_FILE = os.path.join(DIRNAME, 'data/dataset_multidim.hdf5')
DATASET_CHUNKED_FILE = os.path.join(DIRNAME, 'data/chunked.hdf5')

# Define a fixture that opens the chunked file once
@pytest.fixture(scope="module")
def chunked_file():
    with pyfive.File(DATASET_CHUNKED_FILE) as hfile:
        yield hfile 

def test_dataset_indexing_contiguous():
    with pyfive.File(DATASET_CONTIGUOUS_FILE) as hfile:
        assert hfile['d'].__orthogonal_indexing__ is False


@pytest.mark.parametrize(
    "index", [
        (slice(None, None, -1), slice(None, None, -1)),
        (slice(None), slice(None, None, -2)),
        (..., slice(None, None, -2)),
        (slice(None, None, -2), ...),
        (slice(-1, None, -3), ...),
        (slice(-1, None, -3), 0),
        (slice(-1, None, -3), [1, 2, 4]),
        (0, [1, 2, 4]),
        ([1, 2, 4], 1),
        (0, 1),
     ]
)
def test_dataset_indexing_chunked_1(chunked_file, index):
    """Test chunked indexing with -ve step slices and single lists"""
    d = chunked_file['dataset1']
    assert d.__orthogonal_indexing__ is True
    assert d.shape == (21, 16)
    
    array = d[...]
    assert array.shape == d.shape
    
    assert_array_equal(d[index], array[index])

def test_dataset_indexing_chunked_2(chunked_file):
    """Test orthogonal chunked indexing with ints/lists"""
    d = chunked_file['dataset1']
    assert d.__orthogonal_indexing__ is True
    assert d.shape == (21, 16)

    array = d[...]
    assert array.shape == d.shape
  
    assert_array_equal(d[[0, 1], [1, 2, 3]],
                       array[:2, 1:4])

    assert_array_equal(d[[0], [1, 2, 3]],
                       array[0:1, [1, 2, 3]])

    assert_array_equal(d[0, [1, 2, 3]],
                       array[0, [1, 2, 3]])
