import io
import struct

from pyfive.btree import AbstractBTree, BTreeV1RawDataChunks


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


class _DummyFS:
    def __init__(self, payload_by_start):
        self.payload_by_start = payload_by_start
        self.calls = []

    def cat_ranges(self, paths, starts, stops):
        self.calls.append((paths, starts, stops))
        return [self.payload_by_start[s] for s in starts]


def test_get_cat_ranges_fs_support_detection():
    fs = _DummyFS({})
    wrapped = _WrappedFH(fs, "bucket/file.h5")
    out_fs, out_path = AbstractBTree._get_cat_ranges_fs(wrapped)
    assert out_fs is fs
    assert out_path == "bucket/file.h5"

    class NoCatRangesFS:
        pass

    no_support = _WrappedFH(NoCatRangesFS(), "bucket/file.h5")
    out_fs, out_path = AbstractBTree._get_cat_ranges_fs(no_support)
    assert out_fs is None
    assert out_path is None


def test_raw_chunk_tree_reads_leaf_nodes_via_cat_ranges(monkeypatch):
    leaf_raw = {
        1000: _build_leaf_node_bytes(
            dims=1,
            entries=[(16, 0, (0,), 7000)],
        ),
        1001: _build_leaf_node_bytes(
            dims=1,
            entries=[(16, 0, (2,), 7001)],
        ),
        2000: _build_leaf_node_bytes(
            dims=1,
            entries=[(16, 0, (4,), 7002)],
        ),
    }
    fs = _DummyFS(leaf_raw)

    tree = BTreeV1RawDataChunks.__new__(BTreeV1RawDataChunks)
    tree.fh = _WrappedFH(fs, "bucket/file.h5")
    tree.dims = 1
    tree.depth = 2
    tree.last_offset = 0
    tree.all_nodes = {
        2: [
            {
                "node_level": 2,
                "addresses": [100, 200],
            }
        ]
    }

    children = {
        100: [1000, 1001],
        200: [2000],
    }

    def fake_read_node(offset, node_level):
        assert node_level == 1
        return {
            "node_level": 1,
            "entries_used": len(children[offset]),
            "addresses": children[offset],
            "keys": [],
        }

    monkeypatch.setattr(tree, "_read_node", fake_read_node)
    monkeypatch.setattr(tree, "_estimate_leaf_node_size", lambda _: len(leaf_raw[1000]))

    tree._read_children()

    assert len(fs.calls) == 1
    paths, starts, stops = fs.calls[0]
    assert paths == ["bucket/file.h5"] * 3
    assert starts == [1000, 1001, 2000]
    assert stops == [
        1000 + len(leaf_raw[1000]),
        1001 + len(leaf_raw[1001]),
        2000 + len(leaf_raw[2000]),
    ]

    assert 0 in tree.all_nodes
    assert [node["addresses"][0] for node in tree.all_nodes[0]] == [7000, 7001, 7002]


def test_raw_chunk_tree_falls_back_when_cat_ranges_unsupported(monkeypatch):
    tree = BTreeV1RawDataChunks.__new__(BTreeV1RawDataChunks)
    tree.fh = object()

    called = {"value": False}

    def fake_super_read_children(self):
        called["value"] = True

    monkeypatch.setattr(AbstractBTree, "_read_children", fake_super_read_children)

    tree._read_children()

    assert called["value"] is True


def test_estimate_leaf_node_size_uses_header_entries_used():
    header_addr = 32
    buf = bytearray(b"\x00" * header_addr)
    buf.extend(struct.pack("<4sBBHQQ", b"TREE", 1, 0, 3, 0, 0))
    fh = io.BytesIO(bytes(buf))

    tree = BTreeV1RawDataChunks.__new__(BTreeV1RawDataChunks)
    tree.fh = fh
    tree.dims = 2

    # Header (24) + entries_used (3) * entry_size (8 + 16 + 8)
    assert tree._estimate_leaf_node_size(header_addr) == 120
