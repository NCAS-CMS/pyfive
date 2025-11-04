"""Test the p5dump executable via p5ncdump utility."""
import os
import shutil

import pyfive
import pytest


def test_which_p5dump():
    """Run the basic which p5dump."""
    wh = shutil.which("p5dump")
    assert "bin/p5dump" in wh


def test_p5dump_cmd():
    """Run a basic p5dump with no/yes file arg."""
    s1 = os.system("p5dump")
    assert s1 != 0
    s2 = os.system("p5dump tests/data/groups.hdf5")
    assert s2 == 0


def test_hdf5(capsys):
    """Run p5dump on a local HDF5 file."""
    hdf5_file = "./tests/data/groups.hdf5"
    pyfive.p5ncdump(hdf5_file)

    captured = capsys.readouterr()
    assert ('File: groups.hdf5' in captured.out)
    assert ('group: sub_subgroup3' in captured.out)


def test_nc(capsys):
    """Run p5dump on a local netCDF4 file."""
    nc_file = "./tests/data/issue23_A.nc"
    pyfive.p5ncdump(nc_file)

    captured = capsys.readouterr()
    assert ('File: issue23_A.nc' in captured.out)
    assert ('q:cell_methods = "area: mean"' in captured.out)
    assert (':Conventions = "CF-1.12"' in captured.out)
