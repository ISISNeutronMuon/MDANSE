.. _file_formats:

Supported File Formats
======================

In the updated MDANSE version, there have been significant changes to the
supported file formats for input and output. This section provides an
overview of these changes and the file formats used by MDANSE.

.. _hdf5:

HDF5 File Format and GUI Integration
-------------------------------------

In the new version of MDANSE, the primary file format for both trajectory
storage and analysis results is `Hierarchical Data Format (HDF5) <https://www.hdfgroup.org/solutions/hdf5/>`_
. HDF5 is a versatile file format designed for efficiently organizing and managing
large data sets. It employs a hierarchical structure, akin to a file system,
and supports n-dimensional arrays with associated metadata attributes. HDF5
is widely adopted, and even `NetCDF version 4 <https://www.unidata.ucar.edu/software/netcdf/netcdf-4/>`_ 
is built on top of HDF5. Using
HDF5 ensures platform independence, efficient data storage, and 
self-contained information within trajectory files.

Furthermore, users can interact with MDANSE through
the GUI to convert trajectories from different formats to the required
HDF5 format, perform analysis and plot results.

.. _text_output:

DAT File Format
-----------------

An alternative output format of Analysis results is in the form of 
`DAT files <https://en.wikipedia.org/wiki/DAT_file>`_, which
are text-based and easily readable. Each DAT file corresponds to a specific
variable generated during the analysis. If the Text option is selected, a
tarball is generated, which contains multiple files, including:

- ``jobinfo.txt``: A text file documenting the analysis options selected during
  the analysis.
- Variable DAT files: Each file is named after the variable it contains and
  includes the following information:
    - Variable name
    - Type of plot (representing plot dimensions)
    - Variable's placement on the x-axis (if plotted on the y-axis in the
      2D/3D Plotter)
    - Units of data
    - Length of the trajectory (indicated as slice:[length])
    - A list of numbers representing the variable data

The DAT format simplifies data sharing and analysis, providing a clear and
human-readable representation of analysis results.

.. _mdanse-scripts:

MDANSE Scripts
--------------------

MDANSE now includes Python scripts that capture the complete analysis setup,
including all selected options. These scripts are designed to be run using
the Python interpreter bundled with MDANSE. Running these scripts automates
the execution of a specific analysis with predefined settings, simplifying
repetitive tasks and ensuring consistency in analysis procedures.

This update streamlines the analysis process and facilitates the reproducibility
of results within MDANSE.

