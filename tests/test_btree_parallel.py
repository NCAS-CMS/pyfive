import io
import struct

from pyfive.btree import BTreeV1, BTreeV1RawDataChunks
from pyfive.h5d import DatasetID


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

    assert fetch_calls == [([1000, 1001, 2000], len(leaf_raw[1000]))]
    assert 0 in tree.all_nodes
    assert [node["addresses"][0] for node in tree.all_nodes[0]] == [7000, 7001, 7002]


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
    dsid._cat_range_allowed = True
    dsid._thread_count = 0

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
    dsid._cat_range_allowed = False
    dsid._thread_count = 2
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
    dsid._cat_range_allowed = False
    dsid._thread_count = 0

    fetch_fn = dsid._make_btree_fetch_fn()
    assert fetch_fn is None

