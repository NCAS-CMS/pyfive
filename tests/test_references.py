"""Unit tests for pyfive references."""

import os
import sys
import subprocess

from numpy.testing import assert_array_equal, assert_raises
import pytest

import pyfive

DIRNAME = os.path.dirname(__file__)
REFERENCES_HDF5_FILE = os.path.join(DIRNAME, "data", "references.hdf5")
MAKE_REFERENCES_SCRIPT = os.path.join(DIRNAME, "make_references_file.py")


@pytest.fixture(scope="module")
def references_hdf5(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("references")
    path = tmp_dir / "references.hdf5"
    subprocess.run([sys.executable, MAKE_REFERENCES_SCRIPT, str(path)], check=True)
    return str(path)


def test_reference_attrs():
    with pyfive.File(REFERENCES_HDF5_FILE) as hfile:
        root_ref = hfile.attrs["root_group_reference"]
        dset_ref = hfile.attrs["dataset1_reference"]
        group_ref = hfile.attrs["group1_reference"]

        # check references
        root = hfile[root_ref]
        assert root.attrs["root_attr"] == 123
        assert root.name == "/"
        assert root.parent.name == "/"

        dset1 = hfile[dset_ref]
        assert_array_equal(dset1[:], [0, 1, 2, 3])
        assert dset1.attrs["dset_attr"] == 456
        assert dset1.name == "/dataset1"
        assert dset1.parent.name == "/"

        group = hfile[group_ref]
        assert group.attrs["group_attr"] == 789
        assert group.name == "/group1"
        assert group.parent.name == "/"


def test_reference_vlen_attr():
    with pyfive.File(REFERENCES_HDF5_FILE) as hfile:
        vlen_ref_attr = hfile.attrs["vlen_refs"]
        root_ref = vlen_ref_attr[0][0]
        dset_ref = vlen_ref_attr[1][0]
        group_ref = vlen_ref_attr[1][1]

        # check references
        root = hfile[root_ref]
        assert root.attrs["root_attr"] == 123
        assert root.name == "/"
        assert root.parent.name == "/"

        dset1 = hfile[dset_ref]
        assert_array_equal(dset1[:], [0, 1, 2, 3])
        assert dset1.attrs["dset_attr"] == 456
        assert dset1.name == "/dataset1"
        assert dset1.parent.name == "/"

        group = hfile[group_ref]
        assert group.attrs["group_attr"] == 789
        assert group.name == "/group1"
        assert group.parent.name == "/"


def test_reference_dataset():
    with pyfive.File(REFERENCES_HDF5_FILE) as hfile:
        ref_dataset = hfile["ref_dataset"]
        root_ref = ref_dataset[0]
        dset_ref = ref_dataset[1]
        group_ref = ref_dataset[2]
        null_ref = ref_dataset[3]

        # check references
        root = hfile[root_ref]
        assert root.attrs["root_attr"] == 123

        dset1 = hfile[dset_ref]
        assert_array_equal(dset1[:], [0, 1, 2, 3])
        assert dset1.attrs["dset_attr"] == 456

        group = hfile[group_ref]
        assert group.attrs["group_attr"] == 789

        with assert_raises(ValueError):
            hfile[null_ref]

        assert bool(root_ref)
        assert bool(dset_ref)
        assert bool(group_ref)
        assert not bool(null_ref)


def test_chunked_reference_dataset():
    with pyfive.File(REFERENCES_HDF5_FILE) as hfile:
        ref_dataset = hfile["chunked_ref_dataset"]
        root_ref = ref_dataset[0]
        dset_ref = ref_dataset[1]
        group_ref = ref_dataset[2]
        null_ref = ref_dataset[3]

        # check references
        root = hfile[root_ref]
        assert root.attrs["root_attr"] == 123

        dset1 = hfile[dset_ref]
        assert_array_equal(dset1[:], [0, 1, 2, 3])
        assert dset1.attrs["dset_attr"] == 456

        group = hfile[group_ref]
        assert group.attrs["group_attr"] == 789

        with assert_raises(ValueError):
            hfile[null_ref]

        assert bool(root_ref)
        assert bool(dset_ref)
        assert bool(group_ref)
        assert not bool(null_ref)


# Region Reference not yet supported by pyfive
"""
def test_region_reference_dataset():

    with pyfive.File(REFERENCES_HDF5_FILE) as hfile:

        regionref_dataset = hfile['regionref_dataset']
        region_ref = regionref_dataset[0]
        null_ref = regionref_dataset[1]

        assert bool(region_ref)
        assert not bool(null_ref)


def test_chunked_region_reference_dataset():

    with pyfive.File(REFERENCES_HDF5_FILE) as hfile:

        regionref_dataset = hfile['chunked_regionref_dataset']
        region_ref = regionref_dataset[0]
        null_ref = regionref_dataset[1]

        assert bool(region_ref)
        assert not bool(null_ref)


def test_region_reference_attrs():

    with pyfive.File(REFERENCES_HDF5_FILE) as hfile:
        region_ref = hfile.attrs['dataset1_region_reference']

        dset1 = hfile['dataset1']
        subset = dset1[region_ref]
        assert_array_equal(subset, [0, 2])
"""


def test_uninitialized_references(references_hdf5):
    with pyfive.File(references_hdf5) as hfile:
        # testing id of connected dimension
        assert hfile[hfile["foo1"].attrs["DIMENSION_LIST"][0][0]].id == hfile["x"].id
        # test empty aka NULL return
        assert hfile["foo1"].attrs["DIMENSION_LIST"][1].tolist() == []
