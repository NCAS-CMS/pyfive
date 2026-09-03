import os

import pytest

import pyfive
from pyfive.core import InvalidHDF5File

DIRNAME = os.path.dirname(__file__)
NETCDF3_FILE = os.path.join(DIRNAME, "data", "netcdf3_eg.nc3")


def test_read_netcdf3():
    with pytest.raises(InvalidHDF5File, match="NetCDF3 files are not supported"):
        with pyfive.File(NETCDF3_FILE):
            pass
