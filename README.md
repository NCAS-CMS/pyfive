[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/Naereen/StrapDown.js/graphs/commit-activity)
[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)
[![Test](https://github.com/NCAS-CMS/pyfive/actions/workflows/pytest.yml/badge.svg)](https://github.com/NCAS-CMS/pyfive/actions/workflows/pytest.yml)
[![codecov](https://codecov.io/gh/NCAS-CMS/pyfive/graph/badge.svg?token=3In5JuzeGK)](https://codecov.io/gh/NCAS-CMS/pyfive)

![pyfive-logo](https://github.com/NCAS-CMS/pyfive/blob/main/doc/figures/Pyfive-logo.jpg)

pyfive : A pure Python HDF5 file reader
=======================================

pyfive is an open source library for reading HDF5 files written using
pure Python (no C extensions). The package is still in development and not all
features of HDF5 files are supported.

pyfive aims to support the same API as [`h5py`](https://github.com/h5py/h5py)
for reading files. Cases where a file uses a feature that is supported by `h5py`
but not pyfive are considered bug and should be reported in our [Issues](https://github.com/NCAS-CMS/pyfive/issues).
Writing HDF5 is not a goal of pyfive and portions of the API which apply only to writing will not be
implemented.

Dependencies
============

pyfive is tested to work with Python 3.10 to 3.13.  It may also work
with other Python versions.

The only dependencies to run the software besides Python is NumPy.

Install
=======

pyfive can be installed using pip using the command::

    pip install pyfive

conda package are also available from conda-forge which can be installed::

    conda install -c conda-forge pyfive

To install from source in your home directory use::

    python setup.py install --user

The library can also be imported directly from the source directory.


Development
===========

git
---

You can check out the latest pyfive souces with the command::

    git clone https://github.com/NCAS-CMS/pyfive.git

testing
-------

pyfive comes with a test suite in the ``tests`` directory.  These tests can be
exercised using the commands ``pytest`` from the root directory assuming the
``pytest`` package is installed.

Conda-feedstock
===============

Package repository at [conda feedstock](https://github.com/conda-forge/pyfive-feedstock)

Codecov
=======

Test coverage assessement is done using [codecov](https://app.codecov.io/gh/NCAS-CMS/pyfive/)

Documentation
=============

Build locally with Sphinx::

    sphinx-build -Ea doc doc/build
