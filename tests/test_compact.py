import numpy as np
import pytest
from numpy.testing import assert_array_equal

import pyfive
import h5py


def test_compact_dataset_hdf5(name, data):
    with pyfive.File(name) as hfile:
        # check data
        dset1 = hfile["compact"]
        assert_array_equal(dset1[...], data)


@pytest.fixture(scope="module")
def data():
    return np.array([1, 2, 3, 4], dtype=np.int32)


@pytest.fixture(scope="module")
def name(data, modular_tmp_path):
    name = modular_tmp_path / "compact.hdf5"

    f = h5py.File(name, "w", libver="earliest")
    dtype = h5py.h5t.NATIVE_INT32
    space = h5py.h5s.create_simple(data.shape)
    dcpl = h5py.h5p.create(h5py.h5p.DATASET_CREATE)
    dcpl.set_layout(h5py.h5d.COMPACT)
    dset_id = h5py.h5d.create(f.id, b"compact", dtype, space, dcpl=dcpl)
    dset_id.write(h5py.h5s.ALL, h5py.h5s.ALL, data)
    f.close()

    return name
