Optimising speed of data access
******************************* 

HDF5 files can be large and complicated, with complex internal structures which can introduce signficant overheads when accessing the data.

These complexities (and the overheads they introduce) can be mitigated by optimising how you access the data, but this requires an understanding of 
how the data is stored in the file and how the data access library (in this case ``pyfive``) works.

The data storage complexities arise from two main factors: the use of chunking, and the way attributes are stored in the files

**Chunking**: HDF5 files can store data in chunks, which allows for more efficient access to large datasets. 
However, this also means that the library needs to maintain an index (a "b-tree") which relates the position in coordinate space to where each chunk is stored in the file.
There is a b-tree index for each chunked variable, and this index can be scattered across the file, which can introduce overheads when accessing the data.

**Attributes**: HDF5 files can store attributes (metadata) associated with datasets and groups, and these attributes are stored in a separate section of the file.
Again, these can be scattered across the files.


Optimising the files themselves
-------------------------------

Optimal access to data occurs when the data is chunked in a way that matches the access patterns of your application, and when the
b-tree indexes and attributess are stored contiguously in the file.  

Users of ``pyfive`` will always confront data files which have been  created by other software, but if possible, it is worth exploring whether 
the `h5repack <https://docs.h5py.org/en/stable/special.html#h5repack>`_ tool can 
be used to make a copy of the file which is optimised for access by using sensible chunks and to store the attributes and b-tree indexes contiguously.
If that is possible, then all access will benefit from fewer calls to storage to get the necessary metadata, and the data access will be faster.


Avoiding Loading Information You Don't Need
----------------------------------------

In general, the more information you load from the file, the slower the access will be. If you know the variables you need, then don't iterate
over the variables, instantiate them directly.

For example, instead of doing:
.. code-block:: python      

    import pyfive

    with pyfive.File("data.h5", "r") as f:
        variables = [f for var in f]
        print("Variables in file:",variables)
        temp=variables['temp']

You can do:

.. code-block:: python 
    import pyfive
    with pyfive.File("data.h5", "r") as f:
        temp = f['temp']            

You might do the first when finding out what is in the file, but once you know what you need, it is much more efficient to access the variables directly.
That avoids a lot of loading of metadata and attributes that you don't need, and speeds up the access to the data.


Parallel Data Access
----------------------

Unlike ``h5py``, ``pyfive`` is designed to be thread-safe, and it is possible to access the same file from multiple threads without contention.
This is particularly useful when working with large datasets, as it allows you to read data in parallel without blocking other threads.

For example, you can use the `concurrent.futures` module to read data from multiple variables in parallel:

.. code-block:: python

    import pyfive
    from concurrent.futures import ThreadPoolExecutor

    variable_names = ["var1", "var2", "var3"]

    with pyfive.File("data.h5", "r") as f:

        def get_min_of_variable(var_name):
            dset = f[var_name]
            data = dset[...]  # Read the entire variable
            return data.min()
            
        with ThreadPoolExecutor() as executor:
            results = list(executor.map(get_min_of_variable, variable_names))

    print("Results:", results)


You can do the same thing to parallelise manipuations within the variables, by for example using, ``Dask``, but that is beyond the scope of this document.



