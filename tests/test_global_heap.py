"""Unit tests for pyfive's Global Heap collection reader."""

import io
import struct

import h5py
import pytest
import pyfive
from pyfive.misc_low_level import GLOBAL_HEAP_HEADER_SIZE, GlobalHeap


def build_global_heap_collection(objects, trailing_pad=0):
    """Return the bytes of a valid HDF5 Global Heap collection (GCOL).

    ``objects`` is a list of ``(object_index, object_data)`` pairs. Each object's
    data is padded to an 8-byte boundary, as libhdf5 writes it. ``trailing_pad`` is
    the number of unused free-space bytes appended after the last object. A pad
    smaller than one 16-byte object header cannot hold the index-0 free-space marker
    and is just padding.
    """
    body = b""
    for index, data in objects:
        header = struct.pack("<HHIQ", index, 1, 0, len(data))
        padded = data + b"\x00" * ((-len(data)) % 8)
        body += header + padded
    body += b"\x00" * trailing_pad

    collection_size = GLOBAL_HEAP_HEADER_SIZE + len(body)
    gcol_header = (
        b"GCOL"
        + struct.pack("<B", 1)
        + b"\x00\x00\x00"
        + struct.pack("<Q", collection_size)
    )
    return gcol_header + body


def read_objects(raw):
    return GlobalHeap(io.BytesIO(raw), 0).objects


def test_trailing_padding_smaller_than_header():
    """Free space of < 16 bytes at the end must not be read as an object."""
    raw = build_global_heap_collection([(1, b"hello"), (2, b"abc")], trailing_pad=8)
    assert read_objects(raw) == {1: b"hello", 2: b"abc"}


def test_explicit_free_space_terminator():
    """An index-0 free-space object still stops iteration cleanly."""
    body = (
        struct.pack("<HHIQ", 1, 1, 0, 5)
        + b"hello"
        + b"\x00" * 3
        + struct.pack("<HHIQ", 0, 0, 0, 0)
    )
    collection_size = GLOBAL_HEAP_HEADER_SIZE + len(body)
    raw = (
        b"GCOL"
        + struct.pack("<B", 1)
        + b"\x00\x00\x00"
        + struct.pack("<Q", collection_size)
        + body
    )
    assert read_objects(raw) == {1: b"hello"}


def test_collection_exactly_full():
    """No trailing bytes: every object is parsed and the loop ends at the buffer end."""
    raw = build_global_heap_collection(
        [(1, b"hello"), (2, b"abcdefgh")], trailing_pad=0
    )
    assert read_objects(raw) == {1: b"hello", 2: b"abcdefgh"}


def make_shared_global_heap_file(tmp_path):
    """Create a file where many datasets and attrs point into the same GCOL."""
    path = tmp_path / "shared_global_heap.h5"
    shared = ["alpha", "beta", "gamma"]
    with h5py.File(path, "w") as f:
        for i in range(5):
            ds = f.create_dataset(f"ds{i}", (2,), dtype=h5py.special_dtype(vlen=str))
            ds[:] = [shared[0], shared[1]]
            ds.attrs["row"] = shared
            ds.attrs["other"] = shared
    return path


def test_global_heap_is_cached_per_file(tmp_path, monkeypatch):
    """A GCOL referenced by many datasets should be loaded only once per file."""
    path = make_shared_global_heap_file(tmp_path)
    original = pyfive.misc_low_level.GlobalHeap
    calls = []

    def tracked(fh, offset):
        calls.append(offset)
        return original(fh, offset)

    monkeypatch.setattr(pyfive.misc_low_level, "GlobalHeap", tracked)
    monkeypatch.setattr(pyfive.dataobjects, "GlobalHeap", tracked)

    with pyfive.File(path) as hfile:
        for name in hfile:
            _ = hfile[name].attrs
            _ = hfile[name][:]

    assert len(calls) == 1
    assert len(set(calls)) == 1
    assert len(hfile._global_heaps) == 1


@pytest.mark.parametrize("pad", [1, 4, 8, 15])
def test_sub_header_trailing_pad(pad):
    """Any trailing pad shorter than one object header is tolerated."""
    raw = build_global_heap_collection([(7, b"payload")], trailing_pad=pad)
    assert read_objects(raw) == {7: b"payload"}
