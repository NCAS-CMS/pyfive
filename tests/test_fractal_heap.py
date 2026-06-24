import numpy as np
import h5py
import pytest
from contextlib import nullcontext
import pyfive
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
CMIP_BIG_HEAP_FILE = DATA_DIR / "cmip_bad_eg.nc"


@pytest.fixture(scope="module")
def name(tmp_path_factory):
    return tmp_path_factory.mktemp("temp") / "fractal_heap.hdf5"


@pytest.mark.parametrize("payload_size", [4033, 4032])
@pytest.mark.parametrize("n_attrs", [10, 11])
def test_huge_object(name, payload_size, n_attrs):
    """Tests simpe huge objects"""
    err = nullcontext()

    with h5py.File(name, "w", track_order=True) as f:
        for i in range(n_attrs):
            f.attrs[f"small_{i}"] = np.random.randint(
                low=0, high=255, size=payload_size, dtype=np.uint8
            )

    with h5py.File(name, "r") as f:
        attrs = dict(f.attrs)

    with pyfive.File(name, "r") as f:
        with err:
            attrs2 = f.attrs
            print(attrs2.keys())

            for k, v in attrs.items():
                np.testing.assert_equal(v, attrs2[k])


@pytest.mark.parametrize("n_attrs", [115, 116])
def test_fractal_heap(name, n_attrs):
    # att: the assumptions below might heavily rely on the
    # file layout, heaps sizes and other figures
    # todo: generalize this

    with h5py.File(name, "w", track_order=True) as f:
        # create enough attributes to trigger dense storage
        # and indirect blocks
        # using small payloads to control the block filling
        # 115 attributes with 4032 bytes payload each
        # will not create indirect blocks, 116 attributes will

        # 4032 bytes, small enough for managed space
        # from 4033 this will run into huge object space
        payload_size = 4032
        for i in range(n_attrs):
            f.attrs[f"attr_{i}"] = np.random.randint(
                low=0, high=255, size=payload_size, dtype=np.uint8
            )

    with h5py.File(name, "r") as f:
        attrs = dict(f.attrs)

    with pyfive.File(name, "r") as f:
        print("\n--- debug output for test -----------------------\n")
        # since we can't get any information on the heap object from pyfive
        attr_info = f._dataobjects.find_msg_type(0x0015)
        offset = attr_info[0]["offset_to_message"]
        data = pyfive.core._unpack_struct_from(
            pyfive.dataobjects.ATTR_INFO_MESSAGE, f._dataobjects.msg_data, offset
        )
        heap_address = data["fractal_heap_address"]
        heap = pyfive.misc_low_level.FractalHeap(f._fh, heap_address)

        # nfortunately we can't get anything meaningful out of this
        # to see that we actually read from another indirect block
        # we would need to iterate and keep log of it
        # so here we just see the heap header and our block mapping
        print("heap header:", heap.header)
        print("heap_blocks:", len(heap.blocks), heap.blocks)
        print(heap._indirect_nrows_sub)
        print(heap._max_direct_nrows)

        attrs2 = f.attrs

    for k, v in attrs.items():
        np.testing.assert_equal(v, attrs2[k])


def test_tiny_object(name):
    """Haven't been able to create a file with tiny objects, so we test the decoding directly"""
    heap = pyfive.misc_low_level.FractalHeap.__new__(pyfive.misc_low_level.FractalHeap)

    # Normal tiny encoding: 1 flag byte + payload.
    payload = b"abcde"
    heap._tiny_len_extended = False
    heap.managed = b""
    heap.blocks = []
    heap.fh = None
    heapid = bytes([0x20 | (len(payload) - 1)]) + payload
    assert heap.get_data(heapid) == payload

    # Extended tiny encoding: 2 flag bytes + payload.
    payload = b"abcdefghijklmnopqr"
    heap._tiny_len_extended = True
    encoded_size = len(payload) - 1
    heapid = (
        bytes([0x20 | ((encoded_size & 0x0F00) >> 8), encoded_size & 0x00FF]) + payload
    )
    assert heap.get_data(heapid) == payload


def test_huge_cmip_payload():
    """Test reading a huge object from a real file known to exercise the heap object with a b-tree index"""
    if not CMIP_BIG_HEAP_FILE.exists():
        pytest.skip("cmip_bad_eg.nc fixture not present locally")

    with pyfive.File(CMIP_BIG_HEAP_FILE, "r") as f:
        attrs = f.attrs
        print(attrs.keys())
        assert "history" in attrs
        assert len(attrs["history"]) > 200
        mip_era = attrs["mip_era"]
        if isinstance(mip_era, (bytes, np.bytes_)):
            mip_era = mip_era.decode("utf-8")
        assert mip_era == "CMIP6"
        assert attrs.get("fred") is None
