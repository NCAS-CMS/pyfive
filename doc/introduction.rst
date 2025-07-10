Introduction
************

About Pyfive
============

Pyfive provides a pure Python backend reader for ``h5netcdf``, it also exposes variable b-trees to other downstream software.

Our motivations included thread-safety and performance at scale in a cloud environment. To do this we have implemented versions of some more components of the h5py stack, and in particular, a version of the h5d.DatasetID class, which is now holds all the code which is used for data access (as opposed to attribute access, which still lives in dataobjects). There are a couple of extra methods for exposing the chunk index directly rather than via an iterator and to access chunk info using the zarr indexing scheme rather than the h5py indexing scheme.

The code also includes an implementation of what we have called pseudochunking which is used for accessing a contiguous array which is larger than memory via S3. In essence all this does is declare default chunks aligned with the array order on disk and use them for data access.

There are many small bug fixes and optimisations to support cloud usage, the most important of which is that once a variable is instantiated (i.e. for an open pyfive.File instance f, when you do ``v=f['variable_name']``) the attributes and b-tree are read, and it is then possible to close the parent file (f), but continue to use (v) - and we have test coverage that shows that this usage of v is thread-safe (there is a test which demonstrates this, it's slow, but it needs to be as shorter tests were sporadically passing). (The test harness now includes all the components necessary for testing pyfive accessing data via both Posix and S3).
