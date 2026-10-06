"""Virtual datasets are unsupported: pyfive must raise, not return wrong data."""

import h5py
import numpy as np
import pytest

import pyfive


def test_virtual_dataset_raises(tmp_path):
    for i in range(2):
        with h5py.File(tmp_path / f"src{i}.h5", "w") as f:
            f["x"] = np.arange(5) + 10 * i

    layout = h5py.VirtualLayout(shape=(10,), dtype="i8")
    for i in range(2):
        layout[5 * i : 5 * i + 5] = h5py.VirtualSource(
            str(tmp_path / f"src{i}.h5"), "x", shape=(5,)
        )
    path = tmp_path / "vds.h5"
    with h5py.File(path, "w") as f:
        f.create_virtual_dataset("x", layout)

    with pyfive.File(path) as f:
        with pytest.raises(NotImplementedError):
            f["x"][:]
