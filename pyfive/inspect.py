from pathlib import Path

from numpy import dtype
from pyfive import Dataset, Group, File
import logging
from time import time

def safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except BrokenPipeError:
        raise SystemExit(1)


def clean_types(dtype):
    """Convert a numpy dtype to classic ncdump type string."""
    # Strip endianness (> or <) and map to ncdump types
    kind = dtype.kind
    itemsize = dtype.itemsize
    if kind == "f":  # floating point
        return f"float{itemsize * 8}"
    elif kind == "i":  # signed integer
        return f"int{itemsize * 8}"
    elif kind == "u":  # unsigned integer
        return f"uint{itemsize * 8}"
    elif kind == "S" or kind == "a":  # fixed-length bytes
        return "char"
    else:
        return str(dtype)  # fallback


def collect_dimensions_from_root(root):
    """
    Collect true netCDF-style dimensions from the root group only.

    Returns
    -------
    dims : dict
        Maps dimension name (str) -> size (int)
    """
    dims = {}

    for name in root:
        obj = root.get_lazy_view(name)
        # Must be a dataset to be a dimension scale
        if not isinstance(obj, Dataset):
            continue

        # Must have CLASS="DIMENSION_SCALE" to qualify
        if str(obj.attrs.get("CLASS")) == "b'DIMENSION_SCALE'":
            # NetCDF stores the real dimension name under NAME
            dim_name = obj.attrs.get("NAME").decode()
            if dim_name.startswith("This is a netCDF dimension but not a"):
                dim_name = name
            # Use the first axis of its shape as the dimension size
            size = obj.shape[0] if hasattr(obj, "shape") and obj.shape else None

            # Only add if size makes sense
            if size is not None:
                dims[dim_name] = size

    return dims


def gather_dimensions(obj, alldims, phonys, real_dimensions):
    """
    Gather dimensions from dimension scales if present, and if not,
    infer infer phony dimensions (to behave like netcdf reporting of and HDF5 file).
    For a dump that seems useful even if we are an HDF5 only application.
    Monkey patch these dims alongside existing dimension manager.
    """

    if not hasattr(obj, "__inspected_dims"):
        obj.__inspected_dims = []

    oname = obj.name.split("/")[-1]

    for axis, size in enumerate(obj.shape):
        if obj.dims[axis]:  # real scale exists
            edim = (obj.dims[axis][0].name.split("/")[-1], size)

        elif size in real_dimensions.values():
            dim_name = next(name for name, sz in real_dimensions.items() if sz == size)
            edim = (dim_name, size)
        else:
            # make or reuse a phony dimension name
            if size not in phonys:
                phonys[size] = f"phony_dim_{len(phonys)}"
            pname = phonys[size]
            edim = (pname, size)

        obj.__inspected_dims.append(edim)
        alldims.add(edim)

    return obj, alldims, phonys


def dump_header(obj, indent, real_dimensions, special):
    """Pretty print a group within an HDF5 file (including the root group)"""

    def printattr(name, attrs, ommit=[]):
        """Pretty print a set of attributes"""
        for k, v in attrs.items():
            if k not in ommit:
                if isinstance(v, bytes):
                    v = f'"{v.decode("utf-8")}"'
                elif isinstance(v, str):
                    v = f'"{v}"'
                safe_print(f"{indent}{dindent}{dindent}{name}:{k} = {v} ;")

    dims = set()
    datasets = {}
    groups = {}
    phonys = {}
    log_msgs = []

    t0 = time()

    for name in obj:
        item = obj.get_lazy_view(name)
        if isinstance(item, Dataset):
            if str(item.attrs.get("NAME", "None")).startswith(
                "This is a netCDF dimension but not a"
            ):
                continue
            datasets[name] = item
        elif isinstance(item, Group):
            groups[name] = item

    for ds in datasets.values():
        ds, dims, phonys = gather_dimensions(ds, dims, phonys, real_dimensions)
    if dims:
        safe_print(f"{indent}dimensions:")
    dindent = "        "
    for d in dims:
        safe_print(f"{indent}{dindent}{d[0]} = {d[1]};")

    t1 = time() - t0
    log_msgs.append(f"[pyfive] Inspecting File '{obj.name}' and gathered dimensions in {t1:.4f}s")

    print(f"{indent}variables:")
    for name, ds in datasets.items():

        tv0= time()

        # Variable type
        dtype_str = clean_types(ds.dtype)

        # Dimensions for this variable (use dims if available)
        if hasattr(ds, "__inspected_dims"):
            dim_names = [d[0] for d in ds.__inspected_dims]
            dim_str = "(" + ", ".join(dim_names) + ")" if dim_names else ""
            safe_print(f"{indent}{dindent}{dtype_str} {name}{dim_str} ;")

        # Attributes
        ommit = [
            "CLASS",
            "NAME",
            "_Netcdf4Dimid",
            "REFERENCE_LIST",
            "DIMENSION_LIST",
            "DIMENSION_LABELS",
            "_Netcdf4Coordinates",
        ]

        printattr(name, ds.attrs, ommit)

        if special:
            extras = {
                "_Storage": {0: "Compact", 1: "Contiguous", 2: "Chunked"}[
                    ds.id.layout_class
                ]
            }
            if ds.id.layout_class == 2:
                extras["_n_chunks"] = ds.id.get_num_chunks()
                if extras["_n_chunks"] != 0:
                    extras["_chunk_shape"] = ds.id.chunks
                    extras["_btree_range"] = ds.id.btree_range
                    extras["_first_chunk"] = ds.id.first_chunk
                if ds.compression:
                    extras["_compression"] = ds.compression + f"({ds.compression_opts})"
            printattr(name, extras, [])

        tv1 = time() - tv0
        log_msgs.append(f"[pyfive] Inspected variable '{name}' of type '{dtype(ds.dtype)}' in {t1:.4f}s")

    t2 = time()
    
    if isinstance(obj, File):
        hstr = "// global "
    elif isinstance(obj, Group):
        hstr = f"{indent}// group "
    if obj.attrs:
        safe_print(hstr + "attributes:")
        printattr("", obj.attrs, ["_NCProperties"])

    t3 = time() - t2
    log_msgs.append(f"[pyfive] Inspected attributes of {hstr.strip('// ')} in {t3:.4f}s")

    if groups:
        for g, o in groups.items():
            safe_print(f"{indent}group: {g} " + "{")
            gindent = indent + " "
            dump_header(o, gindent, real_dimensions, special=special)
            safe_print(gindent + "}" + f" // group {g}")

    log_msgs.append(f"[pyfive] dump header completed in {time() - t0:.4f}s")

    return log_msgs



def p5ncdump(file_path, special=False):
    """
    Implements a dump functionality which aims to be similar
    but not idnentical the ncdump utility. The key point of
    difference is that datatypes are reported using their numpy
    names (e.g. float64) and that the -s functinoality (special=True)
    tells us more about the layout of chunked data than ncdump,
    including the location of the beginning and ending of
    each chunk index B-tree, the number of chunks, and the start
    of the first data. These characteristics are documented to
    help with understanding retrieval performance across networks.
    """

    # handle posix and S3 differently
    filename = getattr(file_path, "full_name", None)
    if filename is None:
        filename = file_path
    filename = Path(filename).name

    try:
        t0 = time()
        with File(file_path) as f:
            # we assume all the netcdf 4 dimnnsions, if they exist, are in the root group
            real_dimensions = collect_dimensions_from_root(f)
            t1 = time() - t0
            logging.info(f"[pyfive] Opend file and collected real dimensions from root group in {t1:.4f}s")

            # ok, go for it
            safe_print(f"File: {filename} " + "{")
            indent = ""
            log_msgs = dump_header(f, indent, real_dimensions, special)
            safe_print("}")
            t1 = time() - t0
            for msg in log_msgs:
                logging.info(msg)
            logging.info(f"[pyfive] Completed ncdump of file '{filename}' in {t1:.4f}s")

    except NotImplementedError as e:
        if "unsupported superblock" in str(e):
            raise ValueError("Not an HDF5 or NC4 file!")
