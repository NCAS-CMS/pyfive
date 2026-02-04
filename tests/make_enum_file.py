"""
Create HDF5 files with an enum datatype using
(1) the netcdf interface, and
(2) the h5py interface
"""

import sys
import netCDF4
import h5py
import numpy as np
from pathlib import Path

clouds = ["stratus", "stratus", "missing", "nimbus", "cumulus", "longcloudname"]
selection = ["stratus", "nimbus", "missing", "nimbus", "longcloudname"]
enum_dict = {v: k for k, v in enumerate(clouds)}
enum_dict["missing"] = 255
data = [enum_dict[k] for k in selection]


def create_nc_file(path):
    with netCDF4.Dataset(path, mode="w") as ncd:
        enum_type = ncd.createEnumType(np.uint8, "enum_t", enum_dict)

        # add types for checking comparison
        enum_type2 = ncd.createEnumType(np.uint8, "enum2_t", enum_dict)
        vlen_t = ncd.createVLType(np.int32, "phony_vlen")

        # make axis longer to gain uninitialized values
        dim = ncd.createDimension("axis", 10)
        enum_var = ncd.createVariable(
            "enum_var", enum_type, "axis", fill_value=enum_dict["missing"]
        )
        enum_var[:5] = data


def create_hdf_file(path):
    with h5py.File(path, "w") as hcd:
        dt = h5py.enum_dtype(enum_dict, basetype="i")
        assert h5py.check_enum_dtype(dt) == enum_dict
        ds = hcd.create_dataset("enum_var", data=data, dtype=dt)


if __name__ == "__main__":
    default_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent
    if len(sys.argv) == 1:
        create_nc_file(default_path / "enum_variable.nc")
        create_hdf_file(default_path / "enum_variable.hdf5")
    else:
        if default_path.suffix == ".hdf5":
            create_hdf_file(default_path)
        else:
            create_nc_file(default_path)
