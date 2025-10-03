#! /usr/bin/env python
""" Create a HDF5 file with datasets of many datatypes . """
import sys
import h5py
import numpy as np
from pathlib import Path


def create_file(path):

    with h5py.File(path, 'w') as f:

        # signed integers
        common_signed_args = {
            'shape': (4, ),
            'data': -np.arange(4),
            'track_times': False,
        }

        f["int08_little_type"] = np.dtype('<i1')
        f["int08_little_type2"] = np.dtype('<i1')

        f.create_dataset('int08_little', dtype='<i1', **common_signed_args)
        f.create_dataset('int16_little', dtype='<i2', **common_signed_args)
        f.create_dataset('int32_little', dtype='<i4', **common_signed_args)
        f.create_dataset('int64_little', dtype='<i8', **common_signed_args)

        f.create_dataset('int08_big', dtype='>i1', **common_signed_args)
        f.create_dataset('int16_big', dtype='>i2', **common_signed_args)
        f.create_dataset('int32_big', dtype='>i4', **common_signed_args)
        f.create_dataset('int64_big', dtype='>i8', **common_signed_args)

        # unsigned intergers
        common_unsigned_args = {
            'shape': (4, ),
            'data': np.arange(4),
            'track_times': False,
        }

        f.create_dataset('uint08_little', dtype='<u1', **common_unsigned_args)
        f.create_dataset('uint16_little', dtype='<u2', **common_unsigned_args)
        f.create_dataset('uint32_little', dtype='<u4', **common_unsigned_args)
        f.create_dataset('uint64_little', dtype='<u8', **common_unsigned_args)

        f.create_dataset('uint08_big', dtype='>u1', **common_unsigned_args)
        f.create_dataset('uint16_big', dtype='>u2', **common_unsigned_args)
        f.create_dataset('uint32_big', dtype='>u4', **common_unsigned_args)
        f.create_dataset('uint64_big', dtype='>u8', **common_unsigned_args)

        # floating point
        common_float_args = {
            'shape': (4, ),
            'data': np.arange(4),
            'track_times': False,
        }

        f.create_dataset('float32_little', dtype='<f4', **common_float_args)
        f.create_dataset('float64_little', dtype='<f8', **common_float_args)

        f.create_dataset('float32_big', dtype='>f4', **common_float_args)
        f.create_dataset('float64_big', dtype='>f8', **common_float_args)

        # complex
        common_complex_args = {
            'shape': (1, ),
            'data': 123+456.j,
            'track_times': False,
        }

        f["complex64_little_type"] = np.dtype('<c8')
        f["complex64_little_type2"] = np.dtype('<c8')
        f["complex64_big_type"] = np.dtype('>c8')
        f["complex128_little_type"] = np.dtype('<c16')
        f["complex128_big_type"] = np.dtype('>c16')

        f.create_dataset('complex64_little', dtype='<c8', **common_complex_args)
        f.create_dataset('complex128_little', dtype='<c16', **common_complex_args)

        f.create_dataset('complex64_big', dtype='>c8', **common_complex_args)
        f.create_dataset('complex128_big', dtype='>c16', **common_complex_args)

        # vlen
        for endian in ["<", ">"]:
            for base in ["i", "u", "f"]:
                for width in ["1", "2", "4", "8"]:
                    if base == "f" and width == "1":
                        continue
                    tstr = "".join([endian, base, width])
                    dtype = h5py.vlen_dtype(np.dtype(tstr))
                    f[f"vlen_{tstr}_type"] = dtype
                    ds = f.create_dataset(f"vlen_{tstr}", (4,), dtype=dtype)
                    ds[0] = [0]
                    ds[1] = [0, 1]
                    ds[2] = [0, 1, 2]
                    ds[3] = [0, 1, 2, 3]


if __name__ == "__main__":
    default_path = Path(__file__).parent / "dataset_datatypes.hdf5"
    filepath = Path(sys.argv[1]) if len(sys.argv) > 1 else default_path
    create_file(filepath)