import os

import pyfive
import pytest
import s3fs

from conftest import s3_url_exists


def _load_nc_file(ncvar):
    """
    Get the netcdf file and its b-tree.

    Fixture to test loading an issue file.
    """
    issue_file = "da193a_25_6hr_t_pt_cordex__198807-198807.nc"
    storage_options = {
        "anon": True,
        "client_kwargs": {
            "endpoint_url": "https://uor-aces-o.s3-ext.jc.rl.ac.uk"
        },  # final proxy
    }
    test_file_uri = os.path.join("esmvaltool-zarr", issue_file)
    fs = s3fs.S3FileSystem(**storage_options)
    s3file = fs.open(test_file_uri, "rb")
    nc = pyfive.File(s3file)
    ds = nc[ncvar]

    return ds


JASMIN_ONLINE = s3_url_exists("https://uor-aces-o.s3-ext.jc.rl.ac.uk")


@pytest.mark.skipif(not JASMIN_ONLINE, reason="CEDA S3 object store offline.")
def test_buffer_issue():
    """
    Test the case when the attribute contains no data.

    This happens when DATASPACE is NULL and DATA is empty.
    """
    print("File with issue da193a_25_6hr_t_pt_cordex__198807-198807.nc")
    print("Variable m01s30i111")
    _load_nc_file("m01s30i111")


def test_buffer_issue_ukesm():
    """Test with yet another corner case file."""
    fp = "tests/data/noy_AERmonZ_UKESM1-0-LL_piControl_r1i1p1f2_gnz_200001-200012.nc"
    with pyfive.File(fp) as pfile:
        print(pfile["noy"])
        attrs = pfile["noy"].attrs
        print(len(attrs))
        print(attrs.keys())
