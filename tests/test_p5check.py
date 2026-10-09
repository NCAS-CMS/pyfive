import os
import pathlib

import h5py
import numpy as np
import pytest
import pyfive
from pyfive.btree import BTreeV1RawDataChunks
import s3fs

from pyfive.p5check import check_layout, format_report, main
from tests.conftest import endpoint_uri

DIRNAME = os.path.dirname(__file__)


def _write(path, chunks, shape=(40, 20, 30), **kwargs):
    data = np.arange(np.prod(shape), dtype="f4").reshape(shape)
    with h5py.File(path, "w", **kwargs) as f:
        f.create_dataset("v", data=data, chunks=chunks)
        # data written before a second chunked variable's index is created
        f.create_dataset("w", data=data, chunks=chunks)
        f["small"] = np.arange(3)
    return path


@pytest.fixture(scope="module")
def fragmented(modular_tmp_path):
    return _write(modular_tmp_path / "fragmented.h5", (1, 20, 30))


@pytest.fixture(scope="module")
def clean(modular_tmp_path):
    return _write(
        modular_tmp_path / "clean.h5",
        (10, 20, 30),
        meta_block_size=2**20,
    )


def test_fragmented_and_unit_chunks(fragmented):
    report = check_layout(fragmented)
    assert report.fragmented_metadata
    assert report.unit_chunks
    assert report.n_other == 1
    v = {x.name: x for x in report.variables}["/v"]
    assert v.unit_chunk_axes == (0,)
    assert v.n_chunks == 40


def test_clean(clean):
    report = check_layout(clean)
    assert not report.fragmented_metadata
    assert not report.unit_chunks
    assert not report.has_issue
    assert "No layout problems found." in format_report(report)


def test_unit_chunks_only(modular_tmp_path):
    name = _write(modular_tmp_path / "unit_only.h5", (1, 20, 30), meta_block_size=2**20)
    report = check_layout(name)
    assert report.unit_chunks and not report.fragmented_metadata


def test_fragmented_only(modular_tmp_path):
    name = _write(modular_tmp_path / "frag_only.h5", (10, 20, 30))
    report = check_layout(name)
    assert report.fragmented_metadata and not report.unit_chunks


def test_main(fragmented, capsys):
    assert main([str(fragmented)]) == 0
    out = capsys.readouterr().out
    assert "fragmented metadata" in out
    assert "chunk size one in dimension(s) [0]" in out


def test_main_verbose_and_help(clean, capsys):
    assert main(["-v", str(clean)]) == 0
    assert "ok" in capsys.readouterr().out
    assert main(["-h"]) == 0
    assert "p5check" in capsys.readouterr().out


def test_main_bad_args():
    with pytest.raises(ValueError):
        main([])
    with pytest.raises(ValueError):
        main(["a", "b"])
    with pytest.raises(ValueError):
        main(["--nope", "a"])


def test_unchunked_file():
    report = check_layout(os.path.join(DIRNAME, "data", "earliest.hdf5"))
    assert not report.has_issue


def test_mock_s3(s3fs_s3, fragmented):
    bucket = "P5CHECK_BUCKET"
    s3fs_s3.mkdir(bucket)
    s3fs_s3.put(pathlib.Path(fragmented), bucket)
    s3 = s3fs.S3FileSystem(
        anon=False, version_aware=True, client_kwargs={"endpoint_url": endpoint_uri}
    )
    with s3.open(f"{bucket}/{fragmented.name}", "rb") as f:
        report = check_layout(f)
    assert report.fragmented_metadata and report.unit_chunks


@pytest.mark.parametrize("fixture", ["fragmented", "clean"])
def test_sampled_matches_full(fixture, request):
    name = request.getfixturevalue(fixture)
    fast, full = check_layout(name), check_layout(name, full=True)
    assert fast.fragmented_metadata == full.fragmented_metadata
    assert fast.unit_chunks == full.unit_chunks
    for a, b in zip(fast.variables, full.variables):
        assert a.btree_range == b.btree_range
        assert a.n_chunks == b.n_chunks
        assert a.first_chunk >= b.first_chunk


def test_multilevel_btree_not_fully_read(modular_tmp_path):
    # enough chunks for the b-tree to have internal nodes above the leaves
    name = modular_tmp_path / "deep.h5"
    with h5py.File(name, "w") as f:
        f.create_dataset("v", data=np.arange(5000, dtype="f4"), chunks=(1,))
    fast, full = check_layout(name), check_layout(name, full=True)
    assert fast.variables[0].btree_range == full.variables[0].btree_range
    assert fast.variables[0].n_chunks == 5000
    assert fast.unit_chunks

    with pyfive.File(name) as f:
        address = f.get_lazy_view("v").id._index_params.chunk_address
    with open(name, "rb") as fh:
        tree = BTreeV1RawDataChunks(fh, address, 2, read_leaves=False)
    assert tree.depth >= 1
    assert 0 not in tree.all_nodes
    assert len(tree.leaf_addresses) > 1
