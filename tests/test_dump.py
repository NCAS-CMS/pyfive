import pytest
from pyfive.p5dump import main
import os


DIRNAME = os.path.dirname(__file__)
EARLIEST_HDF5_FILE = os.path.join(DIRNAME, "data", "earliest.hdf5")

#
# A standard nicely behaved netcdf4 file is tested in test_mock_s3fs
# Kill two birds with one stone there.
#


def test_old_hd5_with_groups(capsys):
    filename = EARLIEST_HDF5_FILE

    # No exception means success
    assert main([filename]) == 0

    captured = capsys.readouterr()

    # currently failing
    assert "phony_dim_0" in captured.out
    assert "dataset3(phony_dim" in captured.out
    assert 'attr5 = "Test"' in captured.out


# Test: script -s filename (special mode)
def test_main_special_real():
    filename = EARLIEST_HDF5_FILE
    assert main(["-s", filename]) == 0


# Test: -h should print help
def test_main_help_real(capsys):
    main(["-h"])
    captured = capsys.readouterr()
    assert "Provides some of the functionality" in captured.out


# Test: no filename → error
def test_main_no_args_real():
    with pytest.raises(ValueError):
        main([])


# Test: invalid flag → error
def test_main_invalid_args_real():
    with pytest.raises(ValueError):
        main(["-x", "file.nc"])
