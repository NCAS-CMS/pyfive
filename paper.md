---
title: 'pyfive: A pure-Python HDF5 reader'
tags:
  - Python
  - Atmospheric Science
  - Physics
  - Climate Model Data
  - Engineering
authors:
  - name: Bryan N. Lawrence
    orcid: 0000-0001-9262-7860
    affiliation: "1,2"  # (Multiple affiliations must be quoted)
  - name: Ezequiel Cimadevilla
    orcid: 0000-0002-8437-2068
    affiliation: 3
  - name: Wout De Nolf
    affiliation: 4
    orcid: 0000-0003-2258-9402
  - name: David Hassell
    orcid: 0000-0002-5312-4950
    affiliation: "1,2"
  - name: Jonathan Helmus
    affiliation: 5
  - name: Benjamin Hodel
    affiliation: 8
  - name: Brian Maranville
    orcid: 0000-0002-6105-8789
    affiliation: 6
  - name: Kai Mühlbauer
    orcid: 0000-0001-6599-1034
    affiliation: 7
  - name: Valeriu Predoi
    orcid: 0000-0002-9729-6578
    affiliation: "1,2"
affiliations:
 - name: National Center for Atmospheric Science (NCAS), United Kingdom.
   index: 1
   ror: 01wwwe276
 - name: Department of Meteorology, University of Reading, Reading, United Kingdom.
   index: 2
   ror: 05v62cm79
 - name: Instituto de Física de Cantabria (IFCA), CSIC-Universidad de Cantabria, Santander, Spain.
   index: 3
 - name:  European Synchrotron Radiation Facility (ESRF), Grenoble, France.
   index: 4
 - name: Astral Software Inc
   index: 5
 - name: NIST Center for Neutron Research
   index: 6
 - name: Institute of Geosciences, Meteorology Section, University of Bonn, Germany.
   index: 7
 - name: No affiliation.
   index: 8

date: 14 December 2025
bibliography: paper.bib

---

# Summary

`pyfive` (<https://pyfive.readthedocs.io/en/latest/>) is an open-source thread-safe pure Python package for reading data stored in HDF5. 
While it is not a complete implementation of all the specifications and capabilities of HDF5, it includes all the core functionality necessary to read gridded datasets, whether stored contiguously or with chunks.
All data access is fully lazy, the data is only read from storage when the numpy data arrays are manipulated. Originally developed some years ago, the package has recently been upgraded to support lazy access, and to add missing features necessary for handling all the environmental data known to the authors. 
It is now a realistic option for production data access in environmental science and more widely. 
The API is based on that of `h5py` (which is a Python shimmy over the HDF5 C-library, and hence is not thread-safe), with some API extensions to help optimise remote access. 
With these extensions, coupled with thread safety, many of the limitations precluding the efficient use of HDF5 (and netCDF4) on cloud storage have been removed.

# Statement of need

HDF5[^1][@FolEA11] is probably the most important data format in physical science.
It is particularly important in environmental science given the fact that netCDF4[^2][@Rew06] is HDF5 under the hood. 
From satellite missions, to climate models and radar systems, the default binary format has been HDF5 for decades. 
While newer formats are starting to get mindshare, there are petabytes, if not exabytes, of existing HDF5, and there are still many good use-cases for creating new data in HDF5. 
However, despite the history, there are few libraries for reading HDF5 file data that do not depend on the official HDF5 library maintained by the HDF Group, and in particular, apart from `pyfive`, in Python there are none that cover the needs of environmental science. 
While the HDF5 c-library is reliable and performant, and battle-tested over decades, there are some caveats to depending upon it: 
Firstly, it is not thread-safe,  secondly, the code is large and complex, and should anything happen to the financial stability of the HDF5 Group, it is not obvious the C-code could be maintained. 
Finally, the code complexity also meant that it is not suitable for developing bespoke code for data recovery in the case of partially corrupt data. 
From a long-term curation perspective both of these last two constraints are a concern. 

The issues of the dependency on a complex code maintained by one private company in the context of maintaining data access (over decades, and potentially centuries), can only be mitigated by ensuring that the data format is well documented, that data writers use only the documented features, and that public code exists which can be relatively easily maintained. 
The HDF5group have provided good documentation for HDF5, but while there is a community of developers beyond the HDF5 group, recent events suggest that given most of those developers and their existing funding are US based, some spreading of risk would be desirable. 
To that end, a pure Python code covering the core HDF5 features of interest to the target scientific community, which is relatively small and maintained by an international constituency provides some assurance that the community can maintain HDF5 access for the foreseeable future. 
A pure Python code also makes it easier to develop scripts which can work around data and metadata damage should they occur, and has the additional advantage of being able to be deployed in resource or operating-system constrained environments (such as mobile).


[^1]: https://www.hdfgroup.org/solutions/hdf5/
[^2]: https://www.unidata.ucar.edu/software/netcdf

# Current Status


The original implementation of `pyfive` (by JH), which included all the low-level functionality to deal with the internals of an HDF5 file was developed with POSIX access in mind. 
The recent upgrades were developed with the use-cases of performant remote access to curated data as the primary motivation - including full support for lazy loading only parts of chunked datasets as they are needed.

Thread safety has become a concern given the wide use of Dask[^3] in Python based analysis workflows, and this, coupled with a lack of user knowledge about how to efficiently use HDF5, has led to a community perception that HDF5 is not fit for remote access (especially on cloud storage).
``pyfive`` addresses thread safety by bypassing the underlying HDF5 c-library and
addresses some of the issues with remote access by optimising access to
internal file metadata (in particular, the chunk indexes) and by supporting the determination of whether or not a given file is cloud optimised. 

To improve internal metadata access,`pyfive` now supports several levels of "laziness" for instantating chunked datasets (variables). The default method preloads internal indices to make parallellism more efficient, but a completely lazy option without index loading is possible. Neither load data until it is requested.

To be fully cloud optimised, files needs sensible chunking, and variables need contiguous indices. Chunking has been, and is easy to determine.
`pyfive` now also provides simple methods to expose information about internal file layout - both in API extensions, and via a new `p5dump` utility packaged with the `pyfive` library[^4]. Either method allows one to determine whether the key internal "b-tree" indices are contiguous in storage, and to determine the parameters necessary to rewrite the data with contiguous indices.
While `pyfive` itself cannot rewrite files to address chunking or layout, tools such as the HDF5 [repack](https://support.hdfgroup.org/documentation/hdf5/latest/_h5_t_o_o_l__r_p__u_g.html) utility, can do this very efficiently[@HasCim25].

With the use of `pyfive`, suitably repacked and rechunked HDF5 data can now be considered "cloud-optimised", insofar as with lazy loading, 
improved index handling, and thread-safety, there are no "format-induced" constraints on performance during remote access.

[^3]: https://www.dask.org/
[^4]: https://pyfive.readthedocs.io/ 
 
# Acknowledgements

Most of the recent developments outlined have been supported by the UK Met Office and UKRI via 
1) UK Excalibur Exascale programme (ExcaliWork),
2) the UKRI Digital Research Infrastructure programme (WacaSoft), and 
3) the national capability funding of the UK National Center for Atmospheric Science (NCAS). 
Ongoing maintenance of `pyfive` is expected to continue with NCAS national capability funding.

# References
