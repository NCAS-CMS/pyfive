import pyfive as p5
from pathlib import Path

MFILE = Path(__file__).parent / "data" / "Data_20230106_01_014.mat"


def test_matlab():
    """Test user supplied MATLAB file (issue #252)"""
    with p5.File(MFILE, "r") as f:
        assert f.userblock_size == 512
        for ds in f:
            print(ds)
