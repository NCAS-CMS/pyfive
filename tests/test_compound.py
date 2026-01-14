import numpy as np
import h5py
import pytest
import pyfive


@pytest.fixture(scope="module")
def name(tmp_path_factory):
    return tmp_path_factory.mktemp("temp") / "compound.hdf5"


def test_compound(name):
    # Define the inner compound with a reference
    # 'ref' is stored as an 8-byte HDF5 object reference
    inner_dtype = np.dtype(
        [
            ("ref", h5py.ref_dtype),
            ("value", np.float64),
        ]
    )

    # Define the middle compound ---
    middle_dtype = np.dtype(
        [
            ("middle_id", np.int32),
            ("inner", inner_dtype),
        ]
    )

    # Define the outer compound ---
    outer_dtype = np.dtype(
        [
            ("outer_id", np.int32),
            ("middle", middle_dtype),
        ]
    )

    with h5py.File(name, "w") as f:
        # create a dataset to reference
        target = f.create_dataset("target_data", data=np.arange(5))

        # create data array
        data = np.zeros(3, dtype=outer_dtype)
        data["outer_id"] = [1, 2, 3]
        data["middle"]["middle_id"] = [10, 20, 30]
        data["middle"]["inner"]["value"] = [1.1, 2.2, 3.3]

        # assign references
        for i in range(3):
            data["middle"]["inner"]["ref"][i] = target.ref

        # create dataset with the nested compound type
        dset = f.create_dataset("nested", data=data)

    # --- Read back and dereference ---
    with pyfive.File(name, "r") as f:
        arr = f["nested"][...]

        # dereference an element
        for ref in arr["middle"]["inner"]["ref"]:
            obj = f[ref]
            assert obj.id == f["target_data"].id
            assert str(obj) == str(f["target_data"])
