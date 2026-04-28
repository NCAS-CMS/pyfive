import io
import os
import struct

import fsspec
import pytest
from numpy.testing import assert_array_equal

import pyfive
from pyfive.btree import BTreeV1, BTreeV1RawDataChunks
from pyfive.h5d import DatasetID


DIRNAME = os.path.dirname(__file__)
DATASET_CHUNKED_HDF5_FILE = os.path.join(DIRNAME, "data", "chunked.hdf5")


def _build_leaf_node_bytes(*, dims, entries):
    header = struct.pack("<4sBBHQQ", b"TREE", 1, 0, len(entries), 0, 0)
    body = bytearray()
    for chunk_size, filter_mask, chunk_offset, chunk_address in entries:
        body.extend(struct.pack("<II", chunk_size, filter_mask))
        body.extend(struct.pack("<" + ("Q" * dims), *chunk_offset))
        body.extend(struct.pack("<Q", chunk_address))
    return header + bytes(body)


class _WrappedFH:
    def __init__(self, fs, path):
        self.fh = self
        self.fs = fs
        self.path = path
        self.closed = False


class _DummyFS:
    def __init__(self, payload_by_start):
        self.payload_by_start = payload_by_start
        self.calls = []

    def cat_ranges(self, paths, starts, stops):
        self.calls.append((paths, starts, stops))
        return [self.payload_by_start[s] for s in starts]


def test_read_children_with_fetch_fn_fetches_leaves_once(monkeypatch):
    leaf_raw = {
        1000: _build_leaf_node_bytes(dims=1, entries=[(16, 0, (0,), 7000)]),
        1001: _build_leaf_node_bytes(dims=1, entries=[(16, 0, (2,), 7001)]),
        2000: _build_leaf_node_bytes(dims=1, entries=[(16, 0, (4,), 7002)]),
    }

    tree = BTreeV1RawDataChunks.__new__(BTreeV1RawDataChunks)
    tree.fh = io.BytesIO(b"")
    tree.dims = 1
    tree.depth = 2
    tree.last_offset = 0
    tree.all_nodes = {2: [{"node_level": 2, "addresses": [100, 200]}]}

    children = {100: [1000, 1001], 200: [2000]}

    def fake_read_node(offset, node_level):
        assert node_level == 1
        return {
            "node_level": 1,
            "entries_used": len(children[offset]),
            "addresses": children[offset],
            "keys": [],
        }

    fetch_calls = []

    def fake_fetch(addresses, size):
        fetch_calls.append((list(addresses), size))
        return [leaf_raw[a] for a in addresses]

    monkeypatch.setattr(tree, "_read_node", fake_read_node)
    monkeypatch.setattr(tree, "_leaf_node_size", lambda: len(leaf_raw[1000]))
    tree._fetch_fn = fake_fetch

    tree._read_children()

    header_size = struct.calcsize("<4sBBHQQ")
    assert fetch_calls[0] == ([1000, 1001, 2000], header_size)
    assert fetch_calls[1] == ([1000, 1001, 2000], len(leaf_raw[1000]))
    assert 0 in tree.all_nodes
    assert [node["addresses"][0] for node in tree.all_nodes[0]] == [7000, 7001, 7002]


def test_read_children_with_fetch_fn_handles_variable_leaf_sizes(monkeypatch):
    leaf_raw = {
        1000: _build_leaf_node_bytes(
            dims=1,
            entries=[
                (16, 0, (0,), 7000),
                (16, 0, (2,), 7001),
            ],
        ),
        2000: _build_leaf_node_bytes(dims=1, entries=[(16, 0, (4,), 7002)]),
    }

    tree = BTreeV1RawDataChunks.__new__(BTreeV1RawDataChunks)
    tree.fh = io.BytesIO(b"")
    tree.dims = 1
    tree.depth = 2
    tree.last_offset = 0
    tree.all_nodes = {2: [{"node_level": 2, "addresses": [100]}]}

    def fake_read_node(offset, node_level):
        assert offset == 100
        assert node_level == 1
        return {
            "node_level": 1,
            "entries_used": 2,
            "addresses": [1000, 2000],
            "keys": [],
        }

    def fake_fetch(addresses, size):
        return [leaf_raw[a][:size] for a in addresses]

    monkeypatch.setattr(tree, "_read_node", fake_read_node)
    tree._fetch_fn = fake_fetch

    tree._read_children()

    assert [node["entries_used"] for node in tree.all_nodes[0]] == [2, 1]
    assert [addr for node in tree.all_nodes[0] for addr in node["addresses"]] == [
        7000,
        7001,
        7002,
    ]


def test_read_children_falls_back_when_fetch_fn_none(monkeypatch):
    tree = BTreeV1RawDataChunks.__new__(BTreeV1RawDataChunks)
    tree._fetch_fn = None

    called = {"value": False}

    def fake_super_read_children(self):
        called["value"] = True

    monkeypatch.setattr(BTreeV1, "_read_children", fake_super_read_children)

    tree._read_children()

    assert called["value"] is True


def test_leaf_node_size_uses_first_leaf_header():
    header_addr = 32
    buf = bytearray(b"\x00" * header_addr)
    buf.extend(struct.pack("<4sBBHQQ", b"TREE", 1, 0, 3, 0, 0))
    fh = io.BytesIO(bytes(buf))

    tree = BTreeV1RawDataChunks.__new__(BTreeV1RawDataChunks)
    tree.fh = fh
    tree.dims = 2
    tree.all_nodes = {1: [{"addresses": [header_addr]}]}

    # Header (24) + entries_used (3) * entry_size (8 + 16 + 8)
    assert tree._leaf_node_size() == 120


def test_make_btree_fetch_fn_cat_ranges_case():
    dsid = DatasetID.__new__(DatasetID)
    dsid.posix = False
    dsid.set_parallelism(thread_count=0, cat_range_allowed=True, btree_parallel=True)

    fs = _DummyFS({10: b"abcd", 20: b"efgh"})
    dsid._DatasetID__fh = _WrappedFH(fs, "bucket/file.h5")

    fetch_fn = dsid._make_btree_fetch_fn()
    assert fetch_fn is not None

    out = fetch_fn([10, 20], 4)
    assert out == [b"abcd", b"efgh"]
    assert fs.calls == [(["bucket/file.h5", "bucket/file.h5"], [10, 20], [14, 24])]


def test_make_btree_fetch_fn_pread_case(tmp_path):
    dsid = DatasetID.__new__(DatasetID)
    dsid.posix = True
    dsid.set_parallelism(thread_count=2, cat_range_allowed=False, btree_parallel=True)
    payload = b"abcdefghijklmnopqrstuvwxyz"
    fpath = tmp_path / "pread.bin"
    fpath.write_bytes(payload)
    dsid._filename = str(fpath)

    fetch_fn = dsid._make_btree_fetch_fn()
    assert fetch_fn is not None

    out = fetch_fn([0, 4, 8], 3)
    assert out == [b"abc", b"efg", b"ijk"]


def test_make_btree_fetch_fn_serial_case():
    dsid = DatasetID.__new__(DatasetID)
    dsid.posix = True
    dsid.set_parallelism(thread_count=0, cat_range_allowed=False, btree_parallel=False)

    fetch_fn = dsid._make_btree_fetch_fn()
    assert fetch_fn is None


def test_parallel_pread_matches_serial_results_for_chunked_dataset():
    with pyfive.File(DATASET_CHUNKED_HDF5_FILE) as hfile:
        serial = hfile["dataset1"]
        serial.id.set_parallelism(
            thread_count=0, cat_range_allowed=False, btree_parallel=False
        )
        serial_data = serial[:]
        serial_chunk_info = [
            serial.id.get_chunk_info(i) for i in range(serial.id.get_num_chunks())
        ]

    with pyfive.File(DATASET_CHUNKED_HDF5_FILE) as hfile:
        parallel = hfile["dataset1"]
        parallel.id.set_parallelism(
            thread_count=2, cat_range_allowed=False, btree_parallel=True
        )
        parallel_data = parallel[:]
        parallel_chunk_info = [
            parallel.id.get_chunk_info(i) for i in range(parallel.id.get_num_chunks())
        ]

    assert_array_equal(parallel_data, serial_data)
    assert parallel_chunk_info == serial_chunk_info


def test_parallel_fsspec_cat_ranges_matches_serial_results():
    with pyfive.File(DATASET_CHUNKED_HDF5_FILE) as hfile:
        serial = hfile["dataset1"]
        serial.id.set_parallelism(
            thread_count=0, cat_range_allowed=False, btree_parallel=False
        )
        serial_data = serial[:]
        serial_chunk_info = [
            serial.id.get_chunk_info(i) for i in range(serial.id.get_num_chunks())
        ]

    memfs = fsspec.filesystem("memory")
    mem_path = "/chunked.hdf5"
    with open(DATASET_CHUNKED_HDF5_FILE, "rb") as src:
        memfs.pipe(mem_path, src.read())

    calls = []
    original_cat_ranges = memfs.cat_ranges

    def cat_ranges_spy(paths, starts, stops, *args, **kwargs):
        calls.append((list(paths), list(starts), list(stops)))
        return original_cat_ranges(paths, starts, stops, *args, **kwargs)

    memfs.cat_ranges = cat_ranges_spy

    with memfs.open(mem_path, "rb") as fh:
        with pyfive.File(fh) as hfile:
            ds = hfile["dataset1"]
            ds.id.set_parallelism(
                thread_count=0, cat_range_allowed=True, btree_parallel=True
            )
            fsspec_data = ds[:]
            fsspec_chunk_info = [
                ds.id.get_chunk_info(i) for i in range(ds.id.get_num_chunks())
            ]

    assert calls, "Expected fsspec cat_ranges to be used for leaf-node reads"
    assert_array_equal(fsspec_data, serial_data)
    assert fsspec_chunk_info == serial_chunk_info


def test_parallel_s3fs_cat_ranges_matches_serial_results(s3fs_s3):
    with pyfive.File(DATASET_CHUNKED_HDF5_FILE) as hfile:
        serial = hfile["dataset1"]
        serial.id.set_parallelism(
            thread_count=0, cat_range_allowed=False, btree_parallel=False
        )
        serial_data = serial[:]
        serial_chunk_info = [
            serial.id.get_chunk_info(i) for i in range(serial.id.get_num_chunks())
        ]

    bucket = "PARALLEL_BTREE"
    try:
        s3fs_s3.mkdir(bucket)
    except FileExistsError:
        pass

    s3_key = f"{bucket}/chunked.hdf5"
    s3fs_s3.put(DATASET_CHUNKED_HDF5_FILE, s3_key)

    calls = []
    original_cat_ranges = s3fs_s3.cat_ranges

    def cat_ranges_spy(paths, starts, stops, *args, **kwargs):
        calls.append((list(paths), list(starts), list(stops)))
        return original_cat_ranges(paths, starts, stops, *args, **kwargs)

    s3fs_s3.cat_ranges = cat_ranges_spy

    with s3fs_s3.open(s3_key, "rb") as fh:
        with pyfive.File(fh) as hfile:
            ds = hfile["dataset1"]
            ds.id.set_parallelism(
                thread_count=0, cat_range_allowed=True, btree_parallel=True
            )
            s3_data = ds[:]
            s3_chunk_info = [
                ds.id.get_chunk_info(i) for i in range(ds.id.get_num_chunks())
            ]

    assert calls, "Expected s3fs cat_ranges to be used for leaf-node reads"
    assert_array_equal(s3_data, serial_data)
    assert s3_chunk_info == serial_chunk_info
