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

@pytest.mark.parametrize(
    "index", [
        (slice(None, None, -1), slice(None, None, -1)),
        (slice(None), slice(1000, 1, -2)),
        (..., slice(None, None, -2)),
        (slice(None, None, -2), ...),
        (0, slice(-1, None, -3)),
        (slice(-1, None, -3), 0),
     ]
)
def test_dataset_indexing_chunked_negative_step_slices(chunked_file, index):
    """Test orthogonal chunked indexing with negative step slices"""
    d = chunked_file['dataset1']
    assert d.shape == (21, 16)

    array = d[...]
    assert array.shape == d.shape

    assert_array_equal(d[index], array[index])

def test_dataset_indexing_parse_indices_for_chunks():
    """Test pyfive.indexing.parse_indices_for_chunks"""
    func = pyfive.indexing.parse_indices_for_chunks

    range8 = list(range(8))

    assert func((Ellipsis,), (7, 8, 9)) == (
        (slice(0, 7, 1), slice(0, 8, 1), slice(0, 9, 1)), ()
    )

    assert func((0, slice(6, 0, -2)), (7, 8, 9)) == (
        (0, slice(2, 7, 2), slice(0, 9, 1)), (0,)
    )
    assert range8[slice(6, 0, -2)] == list(reversed(range8[slice(2, 7, 2)]))

    assert func(([1, 2], slice(600, None, -3), ..., 0), (7, 8, 9)) == (
        ([1, 2], slice(1, 8, 3), 0), (1,)
    )
    assert range8[slice(600, None, -3)] == list(reversed(range8[slice(1, 8, 3)]))


