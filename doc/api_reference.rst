API Reference
*************

.. autoclass:: pyfive.File
   :members:
   :noindex:
      
----

.. autoclass:: pyfive.Group
   :members:
   :noindex:

----

.. autoclass:: pyfive.Dataset
   :members:
   :noindex:

----

.. autoclass:: pyfive.Datatype
   :members:
   :noindex:

----

The h5t module
--------------

Partial implementation of some of the lower level h5py API, needed
to support enumerations, variable length strings, and opaque datatypes.

.. autofunction:: pyfive.h5t.check_enum_dtype

.. autofunction:: pyfive.h5t.check_string_dtype

.. autofunction:: pyfive.h5t.check_dtype

.. autofunction:: pyfive.h5t.check_opaque_dtype

.. autoclass:: pyfive.h5t.TypeEnumID
   
