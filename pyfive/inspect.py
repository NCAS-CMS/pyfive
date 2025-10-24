from pathlib import Path

from pyfive import Dataset, Group, File 

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
        if not isinstance(obj,Dataset):
            continue

        # Must have CLASS="DIMENSION_SCALE" to qualify
        if str(obj.attrs.get("CLASS")) == "b'DIMENSION_SCALE'":
            # NetCDF stores the real dimension name under NAME
            dim_name = obj.attrs.get("NAME").decode()
            if dim_name.startswith('This is a netCDF dimension but not a'):
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
   
    if not hasattr(obj,'__inspected_dims'):
        obj.__inspected_dims=[]
   
    oname = obj.name.split('/')[-1]
 
    for axis, size in enumerate(obj.shape):
       
        if obj.dims[axis]:  # real scale exists
            edim = (obj.dims[axis][0].name.split('/')[-1], size)

        elif size in real_dimensions.values():
            dim_name = next(name for name, sz in real_dimensions.items() if sz == size)
            edim = (dim_name, size)
        else:
            # make or reuse a phony dimension name
            if size not in phonys:
                phonys[size] = f"phony_dim_{len(phonys)}"
            pname = phonys[size]
            edim = (pname,size)
 
        obj.__inspected_dims.append(edim)
        alldims.add(edim)

    return obj, alldims, phonys


def dump_header(obj, indent, real_dimensions):
    """ Pretty print a group within an HDF5 file (including the root group) """

    def printattr(attrs, ommit=[]):
        """ Pretty print a set of attributes """
        for k,v in attrs.items():
            if k not in ommit:
                if isinstance(v, bytes):
                    v = f'"{v.decode("utf-8")}"'
                print(f"{indent}{dindent}{dindent}{name}:{k} = {v} ;")

    dims = set()
    datasets = {}
    groups = {}
    phonys = {}

    for name in obj:
        item = obj.get_lazy_view(name)
        if isinstance(item, Dataset):
            if str(item.attrs.get('NAME','None')).startswith('This is a netCDF dimension but not a'):
                    continue
            datasets[name]=item
        elif isinstance(item, Group):
            groups[name]=item


    for ds in datasets.values():
        ds, dims, phonys = gather_dimensions(ds, dims, phonys, real_dimensions)
    if dims:
        print(f"{indent}dimensions:")
    dindent = '        '
    for d in dims:
        print(f'{indent}{dindent}{d[0]} = {d[1]};')
    
    print(f"{indent}variables:")
    for name,ds in datasets.items():
        
        # Variable type
        dtype_str = clean_types(ds.dtype)

        # Dimensions for this variable (use dims if available)
        if hasattr(ds,'__inspected_dims'):
            dim_names = [d[0] for d in ds.__inspected_dims]
            dim_str = "(" + ", ".join(dim_names) + ")" if dim_names else ""
            print(f"{indent}{dindent}{dtype_str} {name}{dim_str} ;")

        # Attributes
        ommit = ['CLASS','NAME','_Netcdf4Dimid',
                 'REFERENCE_LIST','DIMENSION_LIST','DIMENSION_LABELS','_Netcdf4Coordinates']
        
        printattr(ds.attrs, ommit)
       
    if isinstance(obj, File):
        hstr='// global '
    elif isinstance(obj, Group):
        hstr=f'{indent}// group '
    if obj.attrs:
        print(hstr+'attributes:')
        printattr(obj.attrs, ['_NCProperties'])
        
    if groups:
        for g,o in groups.items():
            print(f'{indent}group: {g} '+'{')
            gindent = indent+' '
            dump_header(o,gindent,real_dimensions)
            print(gindent+'}'+f' // group {g}')
   


def p5ncdump(file_path, special=False):

    if special:
        raise NotImplementedError

    # handle posix and S3 differently
    filename = getattr(file_path,'full_name', None)
    if filename is None:
        filename = file_path
    filename = Path(filename).name

    try:
        with File(file_path) as f:

            # we assume all the netcdf 4 dimnnsions, if they exist, are in the root group
            real_dimensions = collect_dimensions_from_root(f)
    
            # ok, go for it
            print(f"File: {filename} "+'{')
            indent = ''
            dump_header(f, indent, real_dimensions)
            print('}')

    except NotImplementedError as e:
        if 'unsupported superblock' in str(e):
            raise ValueError('Not an HDF5 or NC4 file!')