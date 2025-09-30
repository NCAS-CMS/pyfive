import h5py
import numpy as np

f = h5py.File('compact.hdf5', 'w', libver='earliest')
data = np.array([1, 2, 3, 4], dtype=np.int32)
dtype = h5py.h5t.NATIVE_INT32
space = h5py.h5s.create_simple(data.shape)
dcpl = h5py.h5p.create(h5py.h5p.DATASET_CREATE)
dcpl.set_layout(h5py.h5d.COMPACT)
dset_id = h5py.h5d.create(f.id, b"compact", dtype, space, dcpl=dcpl)
dset_id.write(h5py.h5s.ALL, h5py.h5s.ALL, data)

f.close()