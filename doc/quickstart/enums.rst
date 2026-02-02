Enumerations
------------

HDF5 has the concept of an "`enumeration data type`", where integer values are stored in an array, but where those integer
values should be interpreted as the indexes to some string values. 

For example, one could have an enumeration dictionary (`enum_dict`) defined as:

.. code-block:: python

    clouds = ['stratus', 'strato-cumulus', 'missing', 'nimbus', 'cumulus', 'longcloudname']
    enum_dict =  {v:k for k,v in enumerate(clouds)}
    enum_dict['missing'] = 255

And an array of data which looked something like

.. code-block:: python

    cloud_cover = [0, 3, 4, 4, 4, 1, 255, 1, 1]

Which one would expect to interpret as 

.. code-block:: python

    actual_cloud_cover = ['stratus', 'nimbus', 'cumulus', 'cumulus', 'cumulus',
                          'stratus', 'missing', 'strato-cumulus', 'strato-cumulus']

These data are stored in HDF5 using a combination of an integer
valued array and a stored dictionary which is used for the enumeration.
When the data is read, the integer array has a special numpy datatype, with
the enumeration dictionary stored as metadata on the data type.

The enumeration dictionary itself can be stored as a ``Datatype``, but it
doesn't need to be and nor is it necessary to use that datatype to
use an enumeration variable (the enumeration is not stored as a normal data
variable and so can be stored without using a Datatype object in the file). 
So, while finding a Datatype in your HDF5 file is probably an indication
that you have an enumeration (or some other complication) in the file,
it is not necessary to do anything with it if it is an enumeration datatype.

Whether or not there is an enumeration DataType in the file, one can only find out 
if any integer data array read from a data file is linked to an 
enumeration by checking it's data type using :meth:`pyfive.check_enum_dtype` as shown 
in the following example:

.. code-block:: python

    with pyfive.File('myfile.h5') as pfile:
   
        evar = pfile['evar']
        edict = pyfive.check_enum_dtype(evar.dtype)
        if edict is None:
            pass # not an enumeration
        else:
            # for some reason HDF5 defines these in what seems to be the wrong way around,
            # with the string values as keys to the integer indices.
            edict_reverse = {v:k for k,v in edict.items()}
            # assuming evar data is a one dimensional array of integers
            edata = [edict_reverse[k] for k in evar[:]]

In this instance, ``edata`` would now be a array of strings indexed from the enumeration dictionary using
the ``evar`` data as the index values.

.. note::

    ``h5py`` and hence ``pyfive`` have both used an internal numpy dtype metadata feature to implement enumerations.
    ``numpy`` is not clear on the future of this feature, and doesn't promise to transfer metadata with all operations,
    so the output of operations on this integer array may lose the direct link to the enumeration via the dtype. 
    Meanwhile, as well as using the `check_enum_dtype`, you can also get to this dictionary directly yourself, 
    it is available at ``evar.dtype.metadata['enum']``.









