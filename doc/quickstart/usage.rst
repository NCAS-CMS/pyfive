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
working with large datasets in a parallel environment where you might want to close the file to free up resources while still needing to access the data. 

.. note::

    This functionality depends on the fact that the attributes and chunk index of the dataset are read when you first access it, so you can continue to use the dataset
    after closing the file. This is fully lazy (in that no data is read until needed) and thread-safe, and we have tests to ensure that this behavior works correctly 
    even in multi-threaded scenarios. 











