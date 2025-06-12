.. _file_formats:

File Formats
============

In MDANSE 2, there have been significant changes to the
supported file formats for input and output. This section provides an
overview of these changes and the file formats used by MDANSE.

.. _hdf5:

HDF5 Based File Formats
-----------------------

In MDANSE 2, the primary file format for both trajectory (MDT)
storage and analysis (MDA) results are based on the `Hierarchical Data Format (HDF5) <https://www.hdfgroup.org/solutions/hdf5/>`_
. HDF5 is a versatile file format designed for efficiently organizing and managing
large data sets. It employs a hierarchical structure, akin to a file system,
and supports *n*-dimensional arrays with associated metadata attributes. HDF5
is widely adopted, and even `NetCDF version 4 <https://www.unidata.ucar.edu/software/netcdf/netcdf-4/>`_ 
is built on top of HDF5. Using
HDF5 ensures platform independence, efficient data storage, and 
self-contained information within trajectory files.

Trajectories have to be converted to the MDT format before
they can be analysed with MDANSE. Multiple converters
are available in MDANSE to convert outputs of different MD engines
to the MDT format.

The results of MDANSE analysis runs are saved in MDA files.
Contents of the MDA files can be viewed and plotted in the MDANSE GUI.

.. _text_output:

DAT File Format
---------------

An alternative output format of analysis results is in the form of DAT files, which
are text-based and easily readable. Each DAT file corresponds to a specific
variable generated during the analysis. If the TextFormat option is selected, a
tarball is generated, which contains multiple files, including:

- **jobinfo.txt**: A text file documenting the analysis options selected during
  the analysis.
- **DAT Files**: Each file is named after the variable it contains and
  includes the following information:
    - Variable name
    - Type of plot (representing plot dimensions)
    - Variable's placement on the *x*-axis (if plotted on the *y*-axis in the
      2D/3D Plotter)
    - Units of data
    - Length of the trajectory (indicated as ``slice:[length]``)
    - A list of numbers representing the variable data

The DAT format simplifies data sharing and analysis, providing a clear and
human-readable representation of analysis results.

CSV files
---------

Instead of writing the results straight into a text file,
it is also possible to export the results to a CSV file
in post-processing, using the data plotter.
More details on this can be found in :ref:`plotter-csv-output`.

.. _note-on-h5md-files:

H5MD Files
----------

When created according to
`the standard <https://www.nongnu.org/h5md/h5md.html>`_,
H5MD trajectories contain all the information needed by MDANSE
to load, visualise and analyse them. You should be able to
load an H5MD trajectory into MDANSE GUI without converting it
to the MDT format.

Some popular MD engines provide packages for writing H5MD files,
but the resulting files do not include essential information such
as the physical units of time, positions and velocities.
Please try out your
MD engine's H5MD implementation using a very short MD run.
If you are not able to load the resulting H5MD file into MDANSE,
please use the engine's standard trajectory format for other
runs.
