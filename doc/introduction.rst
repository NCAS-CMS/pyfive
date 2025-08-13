Introduction
************

About Pyfive
============

``pyfive`` provides a pure Python HDF reader which has been designed to be a thread-safe drop in replacement
for `h5py <https://github.com/h5py/h5py>`_ with no dependencies on the HDF C library.  It aims to support the same API as 
for reading files. Cases where access to a file uses a feature that is supported by the high-level ``h5py`` interface but not ``pyfive`` are considered bugs and 
should be reported in our `Issues <https://github.com/NCAS-CMS/pyfive/issues>`_. 
Writing HDF5 is not a goal of pyfive and portions of the ``h5py`` API which apply only to writing will not be
implemented.

The motivation for ``pyfive`` development were many, but recent developments prioritised thread-safety, lazy loading, and 
performance at scale in a cloud environment both standalone, 
and as a backend for other software such as `cf-python <https://ncas-cms.github.io/cf-python/>`_, `xarray <https://docs.xarray.dev/en/stable/>`_,  and `h5netcdf <https://h5netcdf.org/index.html>`_. 

As well as the high-level ``h5py`` API we have implemented a version of the ``h5d.DatasetID`` class, which now 
holds all the code which is used for data access  (as opposed to attribute access).  We have also implemented
extra methods (beyond the ``h5py`` API) to expose the chunk index directly (as well as via an iterator) and 
to access chunk info using the ``zarr`` indexing scheme rather than the ``h5py`` indexing scheme. This is useful for avoiding
the need for *a priori* use of ``kerchunk`` to make a ``zarr`` index for a file. 

The code also includes an implementation of what we have called pseudochunking which is used for accessing 
a contiguous array which is larger than memory via S3. In essence all this does is declare default chunks 
aligned with the array order on disk and use them for data access.

There are optimisations to support cloud usage, the most important of which is that 
once a variable is instantiated (i.e. for an open ``pyfive.File`` instance ``f``, when you do ``v=f['variable_name']``) 
the attributes and b-tree (chunk index) are read, and it is then possible to close the parent file (``f``), 
but continue to use (``v``).


.. note::

    We have test coverage that shows that the usage of ``v`` in this way is thread-safe -  the test which demonstrates this is slow, 
    but it needs to be as shorter tests were did not always exercise expected failure modes. 

The pyfive test harness now includes all the components necessary for testing pyfive accessing data via both Posix and S3.


