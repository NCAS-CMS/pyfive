import h5py
import numpy as np
from numpy.testing import assert_array_equal

import pyfive


def test_swift_filter_order(tmp_path):
    path = tmp_path / "swift_filter_order.h5"
    data = np.arange(512, dtype="<i8")

    # Build the pipeline in SWIFT's order via the low-level API.
    dcpl = h5py.h5p.create(h5py.h5p.DATASET_CREATE)
    dcpl.set_chunk((512,))
    dcpl.set_fletcher32()
    dcpl.set_shuffle()
    dcpl.set_deflate(4)

    fid = h5py.h5f.create(str(path).encode(), h5py.h5f.ACC_TRUNC)
    dsid = h5py.h5d.create(
        fid,
        b"d",
        h5py.h5t.py_create(data.dtype, logical=True),
        h5py.h5s.create_simple((512,)),
        dcpl=dcpl,
    )
    dsid.write(h5py.h5s.ALL, h5py.h5s.ALL, data)
    del dsid
    fid.close()

    with h5py.File(path, "r") as f:
        plist = f["d"].id.get_create_plist()
        assert [plist.get_filter(i)[0] for i in range(plist.get_nfilters())] == [
            3,
            2,
            1,
        ]
        assert_array_equal(f["d"][...], data)

    with pyfive.File(path) as f:
        assert_array_equal(f["d"][...], data)
