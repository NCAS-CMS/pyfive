#! /usr/bin/env python
""" Create a HDF5 file with references. """
import sys
import h5py
import numpy as np
from pathlib import Path


def create_file(path):
    with h5py.File(path, 'w') as f:

        # some HDF5 objects for testing
        f.attrs.create('root_attr', 123)

        dset1 = f.create_dataset(
            'dataset1', shape=(4, ), dtype='<i4', data=np.arange(4), track_times=False)
        dset1.attrs.create('dset_attr', 456)
        region_ref = dset1.regionref[::2]

        grp = f.create_group('group1')
        grp.attrs.create('group_attr', 789)

        # references
        f.attrs['root_group_reference'] = f.ref
        f.attrs['dataset1_reference'] = dset1.ref
        f.attrs['group1_reference'] = grp.ref
        f.attrs['dataset1_region_reference'] = region_ref

        # variable length sequence of references sequence
        val = np.empty((2, ), dtype=object)
        ref_dtype = h5py.special_dtype(ref=h5py.Reference)
        val[0] = np.array([f.ref], dtype=ref_dtype)
        val[1] = np.array([dset1.ref, grp.ref], dtype=ref_dtype)
        dt = h5py.special_dtype(vlen=ref_dtype)
        f.attrs.create('vlen_refs', val, dtype=dt)

        # array of references
        ref_dtype = h5py.special_dtype(ref=h5py.Reference)

        ref_dataset = f.create_dataset(
            "ref_dataset", (4,), dtype=ref_dtype, track_times=False)
        ref_dataset[0] = f.ref
        ref_dataset[1] = dset1.ref
        ref_dataset[2] = grp.ref
        # ref_dataset[3] is a Null reference

        chunked_ref_dataset = f.create_dataset(
            "chunked_ref_dataset", (4,), chunks=(2, ), dtype=ref_dtype,
            track_times=False)
        chunked_ref_dataset[0] = f.ref
        chunked_ref_dataset[1] = dset1.ref
        chunked_ref_dataset[2] = grp.ref
        # chunked_ref_dataset[3] is a Null reference

        regionref_dtype = h5py.special_dtype(ref=h5py.RegionReference)

        regionref_dataset = f.create_dataset(
            "regionref_dataset", (2,), dtype=regionref_dtype, track_times=False)
        regionref_dataset[0] = region_ref

        chunked_regionref_dataset = f.create_dataset(
            "chunked_regionref_dataset", (2,), chunks=(1, ), dtype=regionref_dtype,
            track_times=False)
        chunked_regionref_dataset[0] = region_ref
        # chunked_regionref_dataset[1] is a Null reference

        # uninitialized references
        # the following code creates a partly uninitialized attribute
        # DIMENSION_LIST
        # it seems creating attributes the normal way are always fully initialized
        foo_data = np.arange(4).reshape(2, 2)
        f.create_dataset("foo1", data=foo_data)
        f.create_dataset("x", data=np.arange(2))
        f.create_dataset("y", data=np.arange(2))

        f["x"].make_scale()
        f["y"].make_scale()
        f["foo1"].dims[0].attach_scale(f["x"])


if __name__ == "__main__":
    default_path = Path(__file__).parent / "references.hdf5"
    filepath = Path(sys.argv[1]) if len(sys.argv) > 1 else default_path
    create_file(filepath)
