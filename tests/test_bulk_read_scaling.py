"""Bulk fsspec chunk reads must scale roughly linearly with the chunk count."""

import time

import fsspec
import h5py
import numpy as np
import pytest

import pyfive

CHUNK_VALUES = 64


@pytest.fixture
def memory_fs():
    fs = fsspec.filesystem("memory")
    created = []

    def put(tmp_path, nchunks, name):
        data = np.arange(nchunks * CHUNK_VALUES, dtype="f4").reshape(
            nchunks, CHUNK_VALUES
        )
        local = tmp_path / name
        with h5py.File(local, "w") as f:
            f.create_dataset("d", data=data, chunks=(1, CHUNK_VALUES))
        remote = f"/{name}"
        fs.pipe_file(remote, local.read_bytes())
        created.append(remote)
        return remote, data

    yield fs, put
    for path in created:
        fs.rm(path)


def _read(fs, path, selection=Ellipsis, **file_kwargs):
    with fs.open(path, "rb") as fh:
        with pyfive.File(fh, **file_kwargs) as hfile:
            dataset = hfile["d"]
            start = time.perf_counter()
            result = dataset[selection]
            return result, time.perf_counter() - start


@pytest.mark.parametrize("file_kwargs", [{}, {"max_request_block": 1 << 20}])
@pytest.mark.parametrize(
    "selection",
    [Ellipsis, np.s_[::-1], np.s_[::3], np.s_[100:900:7]],
    ids=["all", "reversed", "strided", "strided-subset"],
)
def test_bulk_read_matches_for_any_chunk_order(
    memory_fs, tmp_path, selection, file_kwargs
):
    # Reversed and strided selections request chunks in non-increasing or
    # sparse byte order, so ranges cannot be assumed to be sorted or adjacent.
    fs, put = memory_fs
    path, data = put(tmp_path, 1500, "order.h5")
    result, _ = _read(fs, path, selection, **file_kwargs)
    np.testing.assert_array_equal(result, data[selection])


def test_bulk_read_time_is_linear_in_chunk_count(memory_fs, tmp_path):
    """Matching fetched ranges to chunks was quadratic: 4x chunks cost ~16x.

    Comparing a small and a 4x larger read cancels out machine speed. A linear
    algorithm gives a ratio near 4; the quadratic one gave about 15.
    """
    fs, put = memory_fs
    small_n, large_n = 4000, 16000
    small_path, small_data = put(tmp_path, small_n, "small.h5")
    large_path, large_data = put(tmp_path, large_n, "large.h5")

    small = min(_read(fs, small_path)[1] for _ in range(3))
    result, first = _read(fs, large_path)
    large = min([first] + [_read(fs, large_path)[1] for _ in range(2)])
    np.testing.assert_array_equal(result, large_data)

    ratio = large / small
    assert ratio < 8, (
        f"{large_n} chunks took {large:.3f}s vs {small:.3f}s for {small_n}: "
        f"x{ratio:.1f} for 4x the chunks suggests superlinear scaling"
    )
