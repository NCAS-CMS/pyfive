.. _usage:

*******
Usage
*******

In the main, one uses ``pyfive`` exactly as one would use ``h5py`` so the documentation for ``h5py`` is also relevant. However,
``pyfive`` has some additional API features and optimisations which are noted in the section on "Additional API Features".

.. note:: 

    The ``pyfive`` API does not FULLY implement the entire ``h5py`` API, in particular, there is no support
    for writing files, and most of the low-level ``h5py`` API is not implemented. That said, if you find a case where the 
    high level ``h5py`` API read functionality is not supported by ``pyfive``, please report it as an issue on our 
    `GitHub Issues <https://github.com/ncas-cms/pyfive/issues>`_ page.


Working with Files
==================

``pyfive`` provides a high-level interface to HDF5 files, similar to ``h5py``. You can open an HDF5 file and access its contents using dictionary-like syntax, and 
there is support for lazy loading of datasets on both Posix and S3 filesystems.

Here is a simple example of how to open an HDF5 file and read its contents using ``pyfive``:


.. code-block:: python

    import pyfive

    # Open the file in read-only mode
    with pyfive.File("data.h5", "r") as f:
        # List the top-level groups and datasets
        print("Keys:", list(f.keys()))

        # Access a group
        grp = f["/my_group"]

        # List items inside that group
        print("Items in /my_group:", list(grp.keys()))

        # Access a dataset and inspect its shape and dtype
        dset = grp["my_dataset"]
        print("Shape:", dset.shape)
        print("Data type:", dset.dtype)

        # Read an entire dataset into a NumPy array
        data = dset[...]
        print("First element:", data[0])

In this example:

* ``pyfive.File`` opens the file, returning a file object that behaves like a
  Python dictionary.
* Groups (``Group`` objects) can be accessed using dictionary-like keys.
* Datasets (``Dataset`` objects) expose attributes like ``shape`` and
  ``dtype`` which are loaded when you list them, but the data itself is not loaded from stroage into numpy arrays until you access it. 
  (Lazy loading is discussed in more detail in the section on "Optimising Access Speed".)


.. note::

    If you are used to working with NetCDF4 files (and maybe `netcdf4-python <https://unidata.github.io/netcdf4-python/>`_) the concept of a ``File`` in ``pyfive`` corresponds to
    a NetCDF4 ``Dataset`` (both are read from an actual file), and the ``HDF5``/``pyfive``/``h5py`` concept of a ``Dataset`` corresponds to a NetCDF ``Variable``.
    (At least the notion of a group is semantically similar in both cases! )

Working with datasets
=====================

Most of the time, you will access datasets in a similar way to how you would with ``h5py``. You can read data from a dataset using slicing, and you can also
access attributes associated with the dataset. Here is an example: 

.. code-block:: python

    import pyfive

    with pyfive.File("data.h5", "r") as f:
        # Access a dataset
        dset = f["/my_group/my_dataset"]

        # Read a slice of the dataset
        data_slice = dset[10:20]
        print("Data slice:", data_slice)

        # Access attributes of the dataset
        print("Attributes:", dset.attrs)


One notable feature of ``pyfive`` is that the variable ``dset`` which we have just created is available outside of the context manager (i.e. after the ``with`` block).
This means you can close the file and still work with the dataset, as long as you have instantiated it before closing the file. This is particularly useful for
working with large datasets in a parallel environment where you might want to close the file to free up resources while still needing to access *some* of the data . 

.. note::

    This functionality depends on the fact that the attributes and chunk index of the dataset are read when you first access it, so you can continue to use the dataset
    after closing the file. This is fully lazy (in that no data is read until needed) and thread-safe, and we have tests to ensure that this behavior works correctly 
    even in multi-threaded scenarios. 


Using S3/Object Storage 
=======================

``pyfive`` is designed to work seamlessly with both local filesystems and S3-compatible object storage (and probably any remote storage that supports
the `fsspec <https://filesystem-spec.readthedocs.io/en/latest/>`_ API). However, there are some additional considerations when working with S3, the 
most important of which is the need to use the `s3fs` library to provide a filesystem interface to S3.

Here is a simple example of how to open an HDF5 file stored in S3 and read its contents using ``pyfive``:

.. code-block:: python

    import pyfive
    import s3fs

    S3_URL = "https://mys3server.org"
    
    blocks_MB = 1  # Set the block size for S3 access
    s3params = {
        'endpoint_url': S3_URL,
        'default_fill_cache': False,
        'default_cache_type':"readahead",
        'default_block_size': blocks_MB * 2**20
    }
    fs = s3fs.S3FileSystem(anon=True, **s3params)

    # now we can open the file using the S3 filesystem
    uri = 'mybucket/'+filename
    with fs.open(uri,'rb') as s3file:
        with pyfive.File(s3_file, "r") as f:
            dset = f["/my_group/my_dataset"]
        data = dset[10:20]
        print("Data slice from S3:", data)

.. note::

    The best `s3fs` parameters to use (`s3params`) will depend on what you are actually doing with the file, as
    discussed in the section on "Optimising Access Speed". The parameters above worked well for accessing 
    small amounts of data from a large file, but you may need to adjust them for your specific use case.

This example also shows that while it is possible to close the file access context manager and still access the datasets,
you will need to ensure that the S3 filesystem is still available. ** TBD: CHECK IF THAT IS STILL TRUE** 










