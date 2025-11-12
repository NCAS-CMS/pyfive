import numpy as np
import pytest

import pyfive
import h5py


def test_consolidated_metadata(name, name_consolidated, data, vname):
    # non consolidated metadata
    with pyfive.File(name) as hfile:
        assert ((hfile[vname].id.btree_range[1] > hfile[vname].id.first_chunk) and (not hfile.consolidated_metadata))

    # all btree nodes before first chunk (aka consolidated metadata)
    with pyfive.File(name_consolidated) as hfile:
        assert ((hfile[vname].id.btree_range[1] < hfile[vname].id.first_chunk) and hfile.consolidated_metadata)


@pytest.fixture(scope='module')
def data():
    return np.arange(365 * 721 * 1440, dtype="f4").reshape((365, 721, 1440))


@pytest.fixture(scope='module')
def vname():
    return "a"


@pytest.fixture(scope='module')
def name(data, vname, modular_tmp_path):
    name = modular_tmp_path / 'non-consolidated-metadata.hdf5'

    with h5py.File(name, 'w') as hfile:
        hfile.create_dataset(vname, dtype="float32", shape=data.shape, chunks=(1, 721, 1440),
                             compression="gzip", shuffle=True)
        # in this way first logical chunk (0,0,0) will not be first physical chunk (byte offset)
        hfile["a"][250:] = data[250:]
        hfile["a"][:250] = data[:250]

    return name


@pytest.fixture(scope='module')
def name_consolidated(data, vname, modular_tmp_path):
    name_co = modular_tmp_path / 'consolidated-metadata.hdf5'

    with h5py.File(name_co, 'w', meta_block_size=2 ** 20) as hfile:
        hfile.create_dataset(vname, dtype="float32", shape=data.shape, chunks=(1, 721, 1440),
                             compression="gzip", shuffle=True)
        # in this way first logical chunk (0,0,0) will not be first physical chunk (byte offset)
        hfile["a"][250:] = data[250:]
        hfile["a"][:250] = data[:250]

    return name_co
