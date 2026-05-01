from pathlib import Path
import pytest
import pyfive

@pytest.fixture(scope="module")
def test_file_path():
    return Path(__file__).parent / "data" / "fractal_heap_no_mci_rlat.nc"

# reported in https://github.com/NCAS-CMS/pyfive/issues/225
def test_consolidated_metadata(test_file_path):
    with pyfive.File(test_file_path) as f:
        assert f.consolidated_metadata
