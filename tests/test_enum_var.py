""" Unit tests for pyfive dealing with an enum variable """

import os
import sys
import subprocess
import pytest
import h5py
import numpy as np

import pyfive

DIRNAME = os.path.dirname(__file__)
ENUMVAR_NC_FILE = os.path.join(DIRNAME, 'enum_variable.nc')
ENUMVAR_H5_FILE = os.path.join(DIRNAME, "data", 'enum_variable.hdf5')
MAKE_ENUM_VARIABLE_SCRIPT = os.path.join(DIRNAME, 'make_enum_file.py')


@pytest.fixture(scope="module")
def enum_variable_nc(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("enum_var")
    path = tmp_dir / "enum_variable.nc"
    subprocess.run([sys.executable, MAKE_ENUM_VARIABLE_SCRIPT, str(path)], check=True)
    return str(path)


def test_read_h5enum_variable():

    with pyfive.File(ENUMVAR_H5_FILE) as pfile:

        pvars = [(k,type(pfile[k])) for k in pfile]
        pdata = pfile['enum_var']

    with h5py.File(ENUMVAR_H5_FILE) as hfile:

        hvars = [(k,type(hfile[k])) for k in hfile]
        hdata = hfile['enum_var']

        assert len(pvars) == len(hvars)

        assert np.array_equal(pdata[:],hdata[:])

def test_enum_dict():

    with h5py.File(ENUMVAR_NC_FILE, 'r') as hfile:
        h5_enum_t = hfile['enum_t']
        h5_evar = hfile['enum_var']
        h5_edict = h5py.check_enum_dtype(h5_evar.dtype)
        h5_reverse = {v: k for k, v in h5_edict.items()}
        h5_vals = [h5_reverse[x] for x in h5_evar[:]]

        print('Enum data type ',h5_enum_t)
        print('ENum data dictionary', h5_edict)
        print('Basic enum variable and data', h5_evar, h5_evar[:])
        print('Actual enum vals', h5_vals)

        with pyfive.File(ENUMVAR_NC_FILE) as pfile:

            p5_enum_t = pfile['enum_t']
            p5_evar = pfile['enum_var']
            p5_edict = pyfive.check_enum_dtype(p5_evar.dtype)

            assert str(h5_enum_t) == str(p5_enum_t), "Enum data types do not match"
            assert p5_evar.dtype == h5_evar.dtype, "Enum variable data types do not match"
            assert p5_evar.shape == h5_evar.shape, "Enum shapes do not match"
            
            assert np.array_equal(h5_evar[:], p5_evar[:]), "Enum stored values do not match"
            assert p5_edict == h5_edict, "Enum dictionaries do not match"


def test_enum_datatype():

    with h5py.File(ENUMVAR_NC_FILE, 'r') as hfile:
        h5_enum_t = hfile['enum_t']

        with pyfive.File(ENUMVAR_NC_FILE) as pfile:

            p5_enum_t = pfile['enum_t']
            
            assert str(h5_enum_t) == str(p5_enum_t)

            assert p5_enum_t.id.enum_valueof('stratus') == 1
            assert p5_enum_t.id.enum_nameof(1) == 'stratus'

            #none of these work as the h5py methods do not follow their documentation AFAIK
            #assert h5_enum_t.id.enum_valueof('stratus') == p5_enum_t.id.enum_valueof('stratus')
            #assert h5_enum_t.id.get_member_value(1) == p5_enum_t.id.get_member_value(1)
            
            assert h5_enum_t.dtype == p5_enum_t.dtype


def test_enum_datatype2(enum_variable_nc):

    with h5py.File(enum_variable_nc, 'r') as hfile:

        h5_enum_t = hfile['enum_t']

        with pyfive.File(enum_variable_nc) as pfile:
            p5_enum_t = pfile['enum_t']

            assert str(h5_enum_t) == str(p5_enum_t)

            assert p5_enum_t.id.enum_valueof('stratus') == 1
            assert p5_enum_t.id.enum_nameof(1) == 'stratus'

            # none of these work as the h5py methods do not follow their documentation AFAIK
            # assert h5_enum_t.id.enum_valueof('stratus') == p5_enum_t.id.enum_valueof('stratus')
            # assert h5_enum_t.id.get_member_value(1) == p5_enum_t.id.get_member_value(1)

            assert h5_enum_t.dtype == p5_enum_t.dtype

            assert isinstance(pfile["enum_t"].id, pyfive.h5t.TypeEnumID)
            assert pfile["enum_t"].id == pfile["enum2_t"].id
            assert pfile["enum_t"].id != pfile["phony_vlen"].id



        

