""" 
Create HDF5 files with an enum datatype using 
(1) the netcdf interface, and
(2) the h5py interface 
"""
from netCDF4 import Dataset
import h5py
import numpy as np

clouds = ['stratus','stratus','missing','nimbus','cumulus','longcloudname']
selection = ['stratus','nimbus','missing','nimbus','longcloudname']
enum_dict = {v:k for k,v in enumerate(clouds)}
enum_dict['missing'] = 255
data = [enum_dict[k] for k in selection]

ncd = Dataset('enum_variable.nc','w')
enum_type = ncd.createEnumType(np.uint8,'enum_t', enum_dict)

dim = ncd.createDimension('axis',5) 
enum_var = ncd.createVariable('enum_var',enum_type,'axis',
                                fill_value=enum_dict['missing'])
enum_var[:] = data
ncd.close()

hcd = h5py.File('enum_variable.hdf5','w')
dt = h5py.enum_dtype(enum_dict,basetype='i')
assert h5py.check_enum_dtype(dt) == enum_dict
ds = hcd.create_dataset('enum_var', data=data, dtype=dt)
hcd.close()

