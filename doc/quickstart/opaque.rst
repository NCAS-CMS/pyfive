Opaque Datasets 
---------------

It is possible to create datasets with opaque datatypes in HDF5. These are
datasets where the data is stored as a sequence of bytes, with no
interpretation of those bytes. This is not a commonly used feature of HDF5,
but it is used in some applications.  The ``h5py`` package supports reading
and writing opaque datatypes, and so ``pyfive`` also supports reading them.

This implementation has only been tested for opaque datatypes that
were created using ``h5py``.

Such opaque datatypes will be transparently read into the same type of
numpy array as was used to write the data. The users should not
need to do anything special to read the data - but may need to do
something special with the data to interpret it once read.
