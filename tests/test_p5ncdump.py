"""Test the p5dump executable via p5ncdump utility."""

import os
import shutil
import pyfive
import subprocess
import tempfile

DIRNAME = os.path.dirname(__file__)


def test_which_p5dump():
    """Run the basic which p5dump."""
    wh = shutil.which("p5dump")
    assert "bin/p5dump" in wh


def test_p5dump_cmd():
    """
    Run p5dump on a test HDF5 file safely, capturing output.
    This currently works fine with pytest from the command
    line but breaks inside visual studio code with a wierd
    numpy error. This lengthy version is en route to debugging
    """

    p5dump = shutil.which("p5dump")
    assert p5dump, "p5dump not found in PATH"
    assert os.access(p5dump, os.X_OK), f"{p5dump} is not executable"

    dfile = os.path.join(os.path.dirname(__file__), "data", "groups.hdf5")
    assert os.path.exists(dfile), f"Test file does not exist: {dfile}"

    with tempfile.TemporaryDirectory() as tmpdir:
        # Copy environment and remove PYTHONPATH to avoid NumPy source tree detection
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)

        result = subprocess.run(
            [p5dump, dfile],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=tmpdir,
            env=env,
        )

        print("cmd:", result.args)
        print("returncode:", result.returncode)
        print("stdout:\n", result.stdout)
        print("stderr:\n", result.stderr)

        assert result.returncode == 0


def test_hdf5(capsys):
    """Run p5dump on a local HDF5 file."""
    hdf5_file = DIRNAME + "/data/groups.hdf5"
    pyfive.p5ncdump(hdf5_file)

    captured = capsys.readouterr()
    assert "File: groups.hdf5" in captured.out
    assert "group: sub_subgroup3" in captured.out


def test_nc(capsys):
    """Run p5dump on a local netCDF4 file."""
    nc_file = "./tests/data/issue23_A.nc"
    pyfive.p5ncdump(nc_file)

    captured = capsys.readouterr()
    assert "File: issue23_A.nc" in captured.out
    assert 'q:cell_methods = "area: mean"' in captured.out
    assert ':Conventions = "CF-1.12"' in captured.out
