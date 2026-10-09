"""
Lightweight check of the layout of chunked data in an HDF5 file, local or remote.

Two characteristics make reads of chunked data from remote storage (HTTP, S3)
slow, and both can be found without reading any actual data:

- *fragmented metadata*: the chunk index (b-tree) of a variable lies beyond the
  start of the first chunk of data in the file, so the index can only be read with many small requests
  scattered through the file.
- *unit chunks*: a dimension (of size greater than one) with a chunk size of one,
  which means a very large number of chunks, and hence a very large index.

Both can usually be fixed (by the owner of the data) with ``h5repack``.
"""

import math
import sys
import signal
from dataclasses import dataclass, field

from pyfive import File, Group, Dataset


@dataclass
class VariableLayout:
    """Layout information for one chunked variable."""

    name: str
    shape: tuple
    chunks: tuple
    n_chunks: int
    btree_range: tuple
    first_chunk: int
    unit_chunk_axes: tuple
    fragmented: bool = False  # index extends past the first chunk of data in the file

    @property
    def has_issue(self):
        return self.fragmented or bool(self.unit_chunk_axes)


@dataclass
class LayoutReport:
    """The result of :func:`check_layout`."""

    source: str
    variables: list = field(default_factory=list)
    n_other: int = 0  # compact, contiguous or empty datasets (nothing to check)

    @property
    def fragmented_metadata(self):
        """True if the chunk index of any variable extends past the first chunk of data in the file."""
        return any(v.fragmented for v in self.variables)

    @property
    def unit_chunks(self):
        """True if any variable has a dimension (of size > 1) with a chunk size of one."""
        return any(v.unit_chunk_axes for v in self.variables)

    @property
    def has_issue(self):
        return self.fragmented_metadata or self.unit_chunks


def _datasets(group, seen):
    """Yield (path, dataset) for all datasets below group, without reading any chunk index."""
    for name in group:
        obj = group.get_lazy_view(name)
        if isinstance(obj, Dataset):
            yield obj.name, obj
        elif isinstance(obj, Group):
            key = id(
                obj._dataobjects
            )  # File caches these, so hard link cycles are caught
            if key not in seen:
                seen.add(key)
                yield from _datasets(obj, seen)


def _check_variable(path, dataset, full):
    dsid = dataset.id
    if dsid.layout_class != 2:
        return None
    if full:
        # There is no point reading a remote index serially if it can be avoided
        dsid.set_parallelism(btree_parallel=True)
        dsid._build_index()
        if dsid.get_num_chunks() == 0:
            return None
        btree_range, first_chunk = dsid.btree_range, dsid.first_chunk
    else:
        scan = dsid._scan_index()
        if scan is None:
            return None
        btree_range, first_chunk = scan[:2], scan[2]
    shape, chunks = tuple(dataset.shape), tuple(dataset.chunks)
    # the most chunks there could be; a sparse dataset may have fewer
    n_chunks = math.prod(-(-s // c) for s, c in zip(shape, chunks))
    return VariableLayout(
        name=path,
        shape=shape,
        chunks=chunks,
        n_chunks=n_chunks,
        btree_range=btree_range,
        first_chunk=first_chunk,
        unit_chunk_axes=tuple(
            i for i, (s, c) in enumerate(zip(shape, chunks)) if c == 1 and s > 1
        ),
    )


def _check_open_file(f, source, full):
    report = LayoutReport(source=source)
    for path, dataset in _datasets(f, {id(f._dataobjects)}):
        variable = _check_variable(path, dataset, full)
        if variable is None:
            report.n_other += 1
        else:
            report.variables.append(variable)
    if report.variables:
        first_data = min(v.first_chunk for v in report.variables)
        for v in report.variables:
            v.fragmented = v.btree_range[1] > first_data
    return report


def check_layout(source, full=False, **storage_options):
    """
    Check the layout of the chunked variables in an HDF5 file.

    ``source`` is a local path, a URL (``https://...`` or ``s3://...``, opened with
    ``fsspec``; ``storage_options`` are passed to the ``fsspec`` filesystem), or an
    already open file-like object. Only metadata is read.

    By default only the internal b-tree nodes, and the first and last leaf of each
    index, are read: that gives the end of every index exactly, but only some of the chunk
    addresses, so a file whose indexes are all before the sampled chunks, but
    not before every chunk, would be missed. ``full=True`` reads every leaf node
    (slow for large indexes) and is exact.

    Returns a :class:`LayoutReport`.
    """
    if hasattr(source, "read"):
        with File(source) as f:
            return _check_open_file(f, str(getattr(source, "path", source)), full)

    source = str(source)
    if "://" not in source:
        with File(source) as f:
            return _check_open_file(f, source, full)

    import fsspec

    fs, path = fsspec.core.url_to_fs(source, **storage_options)
    with fs.open(path, "rb") as fh, File(fh) as f:
        return _check_open_file(f, source, full)


def format_report(report, verbose=False):
    """Return a human readable version of a :class:`LayoutReport`."""
    lines = [f"File: {report.source}"]
    lines.append(
        f"  {len(report.variables)} chunked variable(s), "
        f"{report.n_other} other dataset(s) (not chunked, or empty)"
    )
    for v in report.variables:
        if not (verbose or v.has_issue):
            continue
        lines.append(
            f"  {v.name}: shape={v.shape} chunks={v.chunks} n_chunks={v.n_chunks}"
        )
        if v.fragmented:
            lines.append(
                f"      fragmented metadata: b-tree range {v.btree_range} "
                f"extends past the first chunk of data in the file"
            )
        if v.unit_chunk_axes:
            lines.append(
                f"      chunk size one in dimension(s) {list(v.unit_chunk_axes)}"
            )
        if verbose and not v.has_issue:
            lines.append("      ok")
    if report.fragmented_metadata:
        lines.append(
            "Fragmented metadata: some chunk indexes lie beyond the start of the data; "
            "reading these remotely needs many small requests."
        )
    if report.unit_chunks:
        lines.append(
            "Unit chunks: some dimensions have chunk size one, giving very many chunks "
            "(and a large chunk index)."
        )
    if report.has_issue:
        lines.append(
            "Consider repacking (e.g. h5repack) with consolidated metadata and larger chunks."
        )
    else:
        lines.append("No layout problems found.")
    return "\n".join(lines)


def main(argv=None):
    """
    Check an HDF5 file (local path, https:// or s3:// URL) for chunk layouts which are slow to
    read remotely: fragmented metadata (chunk indexes which continue past the start of the data)
    and dimensions with a chunk size of one. Only metadata is read.

    Usage: p5check [-v] [--full] [--anon] filename
    - v will list all chunked variables, not just those with problems
    - full will read every chunk index in full, which is exact but can be slow
      (by default just the upper levels and two leaves of each index are read)
    - anon will use anonymous access for s3:// URLs
    """
    if argv is None:
        argv = sys.argv[1:]

    verbose = anon = full = False
    args = []
    for arg in argv:
        if arg == "-h":
            print(main.__doc__)
            return 0
        elif arg == "-v":
            verbose = True
        elif arg == "--full":
            full = True
        elif arg == "--anon":
            anon = True
        elif arg.startswith("-"):
            raise ValueError(f"Invalid arguments: {argv}")
        else:
            args.append(arg)

    match args:
        case []:
            raise ValueError("No filename provided")
        case [source]:
            options = {"anon": True} if anon and source.startswith("s3://") else {}
            print(format_report(check_layout(source, full=full, **options), verbose))
            return 0
        case _:
            raise ValueError(f"Invalid arguments: {argv}")


if __name__ == "__main__":
    try:
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except (AttributeError, ValueError):
        pass

    try:
        sys.exit(main())
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
