.. _installation:

************
Installation
************

Conda-mamba environment
-----------------------

Use a Miniconda/Miniforge3 installer to create an environment using
our conda ``environment.yml`` file; download the latest Miniconda3 for Linux installer from
the `Miniconda project <https://docs.conda.io/en/latest/miniconda.html#linux-installers>`_,
install it, then create and activate the Pyfive environment:

.. code-block:: bash

    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
    bash Miniconda3-latest-Linux-x86_64.sh
    (base) conda env create -n activestorage -f environment.yml
    (base) conda activate activestorage

.. note::

    Our dependencies are all from ``conda-forge`` so there is no issue related
    to the buggy (and paid-for) Anaconda main/defaults channel!

Installing Pyfive
--------------------------

The installation then can proceed: installing with ``pip`` and installing ``all`` (ie
installing the development and test install):

.. code-block:: bash

    pip install -e .

After installing, you can run tests via ``pytest -n 2``.

Supported Python versions
-------------------------

We adhere to `SPEC0 <https://scientific-python.org/specs/spec-0000/>`_ and support the following Python versions:

* 3.10
* 3.11
* 3.12
* 3.13

.. note::

    Pyfive is fully compatible with ``numpy >=2.0.0``.
