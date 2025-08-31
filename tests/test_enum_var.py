""" Unit tests for pyfive dealing with an enum variable """

import os
import pytest
import h5py
import numpy as np

import pyfive

DIRNAME = os.path.dirname(__file__)
ENUMVAR_NC_FILE = os.path.join(DIRNAME, 'enum_variable.nc')
ENUMVAR_H5_FILE = os.path.join(DIRNAME, 'enum_variable.hdf5')

def NOtest_read_ncenum_variable():

    with pyfive.File(ENUMVAR_NC_FILE) as hfile:

        for x in hfile: 
            if x == 'enum_t':
                #FIXME:ENUM need to work out warnings we want where (in the interim)
                with pytest.warns(UserWarning,match='^Found '):
                    print(x, hfile[x])
            elif x == 'enum_var':
                print (x, hfile[x].dtype)
                with pytest.raises(NotImplementedError):
                    print(x, hfile[x][:])
                #FIXME:ENUM this should eventually return an array of the basic enum type
            else: 
                print(x, hfile[x])


def test_read_h5enum_variable():

    with pyfive.File(ENUMVAR_H5_FILE) as pfile:

        pdata = [(k,type(pfile[k])) for k in pfile]
        print(pdata)

    with h5py.File(ENUMVAR_H5_FILE) as hfile:

        hdata = [(k,type(hfile[k])) for k in hfile]
        print(hdata)

    assert len(pdata) == len(hdata)

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
           




        

