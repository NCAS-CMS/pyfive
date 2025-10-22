from pathlib import Path
import pyfive
def clean_types(dtype):
    """Convert a numpy dtype to classic ncdump type string."""
    # Strip endianness (> or <) and map to ncdump types
    kind = dtype.kind
    itemsize = dtype.itemsize
    if kind == "f":  # floating point
        return f"float{itemsize*8}"
    elif kind == "i":  # signed integer
        return f"int{itemsize*8}"
    elif kind == "u":  # unsigned integer
        return f"uint{itemsize*8}"
    elif kind == "S" or kind == "a":  # fixed-length bytes
        return "char"
    else:
        return str(dtype)  # fallback


def dump_header(f, filename):

    print(f"File: {filename} "+'{')
    dims = set()
    datasets = {name: f[name] for name in f.keys() if hasattr(f[name], "shape")}
    for ds in datasets.values():
        for dim in ds.dims:
            for scale in dim:
                dims.add((scale.name.split('/')[-1],scale.shape[0]))
    if dims:
        print("dimensions:")
    for d in dims:
        print(f'         {d[0]}={d[1]};')
    
    print("variables:")
    for name,ds in datasets.items():
        
        # Variable type
        dtype_str = clean_types(ds.dtype)

        # Dimensions for this variable (use dims if available)
        if hasattr(ds, "dims") and len(ds.dims) > 0:
            dim_names = [scale.name.split('/')[-1] for dim in ds.dims for scale in dim]
        else:
            # fallback: no dims
            dim_names = []

        dim_str = "(" + ", ".join(dim_names) + ")" if dim_names else ""
        print(f"         {dtype_str} {name}{dim_str};")

        # Attributes
        ommit = ['CLASS','NAME','_Netcdf4Dimid','REFERENCE_LIST','DIMENSION_LIST','_Netcdf4Coordinates']
        for attr_name, attr_val in ds.attrs.items():
            if attr_name not in ommit:
                if isinstance(attr_val, bytes):
                    attr_val = f'"{attr_val.decode("utf-8")}"'
                print(f"              {name}:{attr_name} = {attr_val};")
    print('}')

def p5ncdump(file_path, special=False):

    if special:
        raise NotImplementedError

    # handle posix and S3 differently
    filename = getattr(file_path,'full_name', None)
    if filename is None:
        filename = file_path
    filename = Path(filename).name

    try:
        print('Now going to pyfive')
        with pyfive.File(file_path) as f:
            # Attach dims if not already attached
            print('opened')
            for name in f.keys():
                ds = f[name]   #bugger this is a b-tree read
                if hasattr(ds, "shape") and not hasattr(ds, "dims"):
                    # internally pyfive may attach dims automatically, but safe to attach here
                    ds.dims  # access triggers dimension proxies
            dump_header(f, filename)
    except NotImplementedError as e:
        if 'unsupported superblock' in str(e):
            raise ValueError('Not an HDF5 or NC4 file!')