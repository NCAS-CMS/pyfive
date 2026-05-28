"""Unit tests for pyfive dimension scales."""

import os
import warnings

from numpy.testing import assert_array_equal

import pyfive
from pyfive.high_level import DimensionProxy
from pyfive.inspect import gather_dimensions

DIRNAME = os.path.dirname(__file__)
DIM_SCALES_HDF5_FILE = os.path.join(DIRNAME, "data", "dim_scales.hdf5")


def test_dim_labels():
    with pyfive.File(DIM_SCALES_HDF5_FILE) as hfile:
        # dataset with dimension labels
        dims = hfile["dset1"].dims
        assert dims[0].label == "z"
        assert dims[1].label == "y"
        assert dims[2].label == "x"

        # dataset with no dimension labels
        dims = hfile["dset2"].dims
        assert dims[0].label == ""
        assert dims[1].label == ""
        assert dims[2].label == ""


def test_dim_scales():
    with pyfive.File(DIM_SCALES_HDF5_FILE) as hfile:
        # dataset with dimension scales
        dims = hfile["dset1"].dims

        assert len(dims) == 3

        assert len(dims[0]) == 1
        assert len(dims[1]) == 1
        assert len(dims[2]) == 2

        assert dims[0][0].name == "/z1"
        assert dims[1][0].name == "/y1"
        assert dims[2][0].name == "/x1"
        assert dims[2][1].name == "/x2"

        assert_array_equal(dims[0][0][:], [0, 10, 20, 30])
        assert_array_equal(dims[1][0][:], [3, 4, 5])
        assert_array_equal(dims[2][0][:], [1, 2])
        assert_array_equal(dims[2][1][:], [99, 98])

        # dataset with no dimension scales
        dims = hfile["dset2"].dims

        assert len(dims) == 3

        assert len(dims[0]) == 0
        assert len(dims[1]) == 0
        assert len(dims[2]) == 0


def test_dimension_scale_alias_when_axis_size_mismatch():
    class MockScale:
        def __init__(self):
            self.name = "/time_counter"
            self.shape = (1,)
            self.dtype = "float64"

        def __getitem__(self, key):
            return [3.111696e09]

    class MockDset:
        def __init__(self):
            self.shape = (0, 3606, 4322)
            self.name = "/berg_latent_heat_flux"

    scale = MockScale()
    mock_file = {"ref0": scale}
    proxy = DimensionProxy(MockDset(), mock_file, b"", ["ref0"], 0)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        aliased = proxy[0]

    assert len(caught) == 1
    assert "Using alias 'time_counter_1'" in str(caught[0].message)
    assert aliased.name == "/time_counter_1"
    assert (
        repr(aliased) == '<HDF5 dataset "time_counter_1": shape (1,), type "float64">'
    )
    assert_array_equal(aliased[:], [3.111696e09])


def test_gather_dimensions_conflict_does_not_consume_real_suffix_name(caplog):
    class MockScaleRef:
        def __init__(self):
            self.name = "/time_counter"

    class MockDset:
        def __init__(self):
            self.name = "/berg_latent_heat_flux"
            self.shape = (0,)
            self.dims = [[MockScaleRef()]]

    obj = MockDset()
    alldims = {"time_counter": 1, "time_counter_1": 1}
    phonys = {}
    real_dimensions = {}

    _, updated_dims, _ = gather_dimensions(obj, alldims, phonys, real_dimensions)

    assert obj.__inspected_dims == [("_time_counter_1", 0)]
    assert updated_dims["_time_counter_1"] == 0
    assert "Using alternative name '_time_counter_1'" in caplog.text


def test_gather_dimensions_conflict_uses_next_available_alias_suffix(caplog):
    class MockScaleRef:
        def __init__(self):
            self.name = "/time_counter"

    class MockDset:
        def __init__(self):
            self.name = "/berg_latent_heat_flux"
            self.shape = (0,)
            self.dims = [[MockScaleRef()]]

    obj = MockDset()
    alldims = {"time_counter": 1, "_time_counter_1": 0}
    phonys = {}
    real_dimensions = {}

    _, updated_dims, _ = gather_dimensions(obj, alldims, phonys, real_dimensions)

    assert obj.__inspected_dims == [("_time_counter_2", 0)]
    assert updated_dims["_time_counter_2"] == 0
    assert "Using alternative name '_time_counter_2'" in caplog.text
