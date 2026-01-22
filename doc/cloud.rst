Cloud Optimisation
******************

While ``pyfive`` can only read HDF5 files, it includes some features to help users understand whether it might
be worth rewriting files to make them cloud optimised (as defined by Stern et.al., 2022 [#]_).

To be cloud optimised an HDF5 file needs to have a contiguous index for each 
variable, and the chunks for each variable need to be sensibly chosen and broadly contiguous within the file.
When these criteria are met, indexes can be read efficiently, and middleware such as fsspec can make sensible 
use of readahead caching strategies.

HDF5 data files are often not in this state as information about the number
of variables, the number of chunks per variable, and the compressed size of those variables may not be known as the data 
is being produced (e.g. direct from simulations and instruments writing data as it is generated/acquired).
In such cases the data is almost never chunked along the dimensions being added to as the file is written 
(since it would have to be buffered first).

Of course, once the file is produced, such information is available, and it is possible to repack the file to make it
cloud optimised. 
Metadata can be repacked to the front of the file and variables can be rechunked and made contiguous - 
which is effectively the same process undertaken when HDF5 data is reformatted to other cloud optimised formats.

The HDF5 library provides a tool (`h5repack <https://support.hdfgroup.org/documentation/hdf5/latest/_h5_t_o_o_l__r_p__u_g.html>`_) 
which can do this, provided it is driven with suitable information about required chunk shape and the expected size of metadata fields. 
`pyfive` supports both a method to query whether such repacking is necessary, and to extract necessary parameters.

In the following example we compare and contrast the unpacked and repacked version of a particularly pathological 
file, and in doing so showcase some of the `pyfive` API extensions which help us understand why it is pathological, 
and how to address those issues for repacking.

If we look at some of the output of `p5dump -s` on this file 
(which has surface wind velocity at three hour intervals for one hundred years):

.. code-block:: console

    float64 time(time) ;
                    time:standard_name = "time" ;
                    time:_n_chunks = 292192 ;
                    time:_chunk_shape = (1,) ;
                    time:_btree_range = (31808, 19854095942) ;
                    time:_first_chunk = 9094 ;

    float32 uas(time, lat, lon) ;
                    ...
                    uas:_Storage = "Chunked" ;
                    uas:_n_chunks = 292192 ;
                    uas:_chunk_shape = (1, 143, 144) ;
                    uas:_btree_range = (28672, 19854809382) ;
                    uas:_first_chunk = 36520 ;


We can immediately see that this will be a problematic file! The `b-tree` index is clearly interleaved with the data 
(compare the first chunk address with last index addresses of the two variables), and with a chunk dimension of ``(1,)``, 
any effort to use the time-dimension to locate data of interest will involve a ludicrous number of one number reads 
(all underlying libraries read the data one chunk at a time). 
It would feel like waiting for the heat death of the universe if one was to attempt to manipulate this data stored on an object store! 

It is relatively easy (albeit slow) to use 
`h5repack <https://support.hdfgroup.org/documentation/hdf5/latest/_h5_t_o_o_l__r_p__u_g.html>`_ 
to fix this, for example as is being done for a large model intercomparison experiment [#]_, after which we see:

.. code-block:: console

    float64 time(time) ;
                    time:_Storage = "Chunked" ;
                    time:_n_chunks = 1 ;
                    time:_chunk_shape = (292192,) ;
                    time:_btree_range = (11861, 11861) ;
                    time:_first_chunk = 40989128 ;
                    time:_compression = "gzip(4)" ;
    float32 uas(time, lat, lon) ;
                    ...
                    uas:_Storage = "Chunked" ;
                    uas:_n_chunks = 5844 ;
                    uas:_chunk_shape = (50, 143, 144) ;
                    uas:_btree_range = (18663, 347943) ;
                    uas:_first_chunk = 41041196 ;
                    uas:_compression = "gzip(4)" ;

Now data follows indexes, the time dimension is one chunk, and there is a more sensible number of actual data chunks. 
While this file would probably benefit from splitting into smaller files, now it has a contiguous set of indexes 
it is possible to exploit this data via S3.

All the metadata shown in this dump output arises from ``pyfive`` extensions to the ``pyfive.h5t.DatasetID`` class. 
``pyfive`` also provides a simple flag: ``consolidated_metadata`` for a ``File`` instance, which can take values of 
`True` or `False` for any given file, which simplifies at least the "is the index packed at the front of the file?" 
part of the optimisation question - though inspection of chunking is a key part of the workflow necessary to 
determine whether or not a file really is optimised for cloud usage.

.. [#] Stern et.al. (2022): *Pangeo Forge: Crowdsourcing Analysis-Ready, Cloud Optimized Data Production*,  https://dx.doi.org/10.3389/fclim.2021.782909. 
.. [#] Hassell and Cimadevilla Alvarez (2025): *Cmip7repack: Repack CMIP7 netCDF-4 Datasets*, https://dx.doi.org/10.5281/zenodo.17550920.
