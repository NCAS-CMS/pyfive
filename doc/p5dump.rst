p5dump
******

``pyfive`` includes a command line tool ``p5dump`` which can be used to dump the contents of an HDF5 file to the 
terminal. This is similar to the ``ncdump`` tool included with the NetCDF library, or the ``h5dump`` tool included 
with the HDF5 library, but like the rest of pyfive, is implemented in pure Python without any dependencies on the 
HDF5 C library.

It is not identical to either of these toosl, though the default output is very close to that of ``ncdump``.
When called with `-s` (e.g ``p5dump -s myfile.h5``) the output provides extra information for chunked
datsets, including the locations of the start and end of the chunk index b-tree 
and the location of the first data chunk for that variable. This extra information is useful for understanding
the performance of data access for chunked variables, particularly when accessing data in object stores such as
S3. In general, if one fineds that the b-tree index continues past the first data chunk, access 
performance may be sub-optimal - in this situation, if you have control over the data, you might well
consider using the ``h5repack`` tool from the standard HDF5 distribution to make a copy of the file with the 
chunk index and attributes stored contiguously.  All tools which read HDF5 files will benefit from this.


