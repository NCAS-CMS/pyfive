import os

import pyfive
import s3fs


def _load_nc_file(ncvar):
    """
    Get the netcdf file and its b-tree.

    Fixture to test loading an issue file.
    """
    issue_file = "da193a_25_6hr_t_pt_cordex__198807-198807.nc" 
    storage_options = {
        'key': "f2d55c6dcfc7618b2c34e00b58df3cef",
        'secret': "$/'#M{0{/4rVhp%n^(XeX$q@y#&(NM3W1->~N.Q6VP.5[@bLpi='nt]AfH)>78pT",
        'client_kwargs': {'endpoint_url': "https://uor-aces-o.s3-ext.jc.rl.ac.uk"},  # final proxy
    }
    test_file_uri = os.path.join(
        "bnl",
        issue_file
    )
    fs = s3fs.S3FileSystem(**storage_options)
    s3file = fs.open(test_file_uri, 'rb')
    nc = pyfive.File(s3file)
    ds = nc[ncvar]

    return ds


def test_buffer_issue():
    print("File issue: S3/bnl/da193a_25_6hr_t_pt_cordex__198807-198807.nc")
    print("Variable m01s30i111")
    _load_nc_file('m01s30i111')
