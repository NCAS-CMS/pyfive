""" Unit tests for pyfive's ability to read a file with filter_pipeline v2
(as is found in some new netCDF4 files) """
import os

import h5py
import numpy as np
from numpy.testing import assert_almost_equal
import pytest
import pyfive

DIRNAME = os.path.dirname(__file__)
FILTER_PIPELINE_V2_FILE = os.path.join(DIRNAME, 'data', 'filter_pipeline_v2.hdf5')


@pytest.fixture
def generate_data():
    return np.random.rand(100, 100)


@pytest.mark.flaky(reruns=3, only_rerun="ValueError")
@pytest.mark.parametrize("chunk_size", [None, (10, 10), (20, 20)], ids=lambda x: f"chunk_{x}")
@pytest.mark.parametrize("compression", [None, 9, "lzf"], ids=lambda x: f"compression_{x}")
@pytest.mark.parametrize("shuffle", [True, False], ids=lambda x: f"shuffle_{x}")
@pytest.mark.parametrize("fletcher32", [True, False], ids=lambda x: f"fletcher32_{x}")
def test_hdf5_filters(modular_tmp_path, generate_data, chunk_size, compression, shuffle, fletcher32):
    if compression == "lzf" and chunk_size is None and shuffle is True:
        pytest.xfail(reason="lzf compression requires chunk_size with shuffle=True")

    data = generate_data
    file_name = modular_tmp_path / f"test_{chunk_size}_{compression}_{shuffle}_{fletcher32}.hdf5"

    with h5py.File(file_name, "w") as f:
        f.create_dataset("data", data=data, chunks=chunk_size, shuffle=shuffle, fletcher32=fletcher32, compression=compression)

    with pyfive.File(file_name, 'r') as f:
        assert_almost_equal(f["data"][:], data)

def test_filter_pipeline_descr_v2():

    with pyfive.File(FILTER_PIPELINE_V2_FILE) as hfile:
        assert 'data' in hfile
        d = hfile['data']
        assert d.shape == (10,10,10)
        assert_almost_equal(d[0,0,0], 1.0)

def test_filter_pipeline_compression_opts_v2():

     with pyfive.File(FILTER_PIPELINE_V2_FILE) as hfile:
        assert 'data' in hfile
        d = hfile['data']
        # the point of this test is to ensure we can actually retrieve the compression opts
        x = d.compression_opts