import numpy as np
import h5py
import pytest
from contextlib import nullcontext
import pyfive


@pytest.fixture(scope="module")
def name(tmp_path_factory):
    return tmp_path_factory.mktemp("temp") / "fractal_heap.hdf5"


@pytest.mark.parametrize("payload_size", [4033, 4032])
@pytest.mark.parametrize("n_attrs", [10, 11])
def test_huge_object(name, payload_size, n_attrs):
    # 4032/4033 is the huge object treshold
    # it kicks in, if we have more than 10 attributes
    # todo, this needs more check,
    #  might depend on heap sizes and other figures
    if payload_size == 4033 and n_attrs == 11:
        err = pytest.raises(NotImplementedError)
    else:
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
