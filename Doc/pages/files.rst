.. _file_formats:

How to Guide Supported File Formats
==================================

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
HDF5 ensures platform independence, efficient data storage, and comprehensive
self-contained information within trajectory files.

This transition to HDF5 as the primary storage format enhances data compatibility
and accessibility within MDANSE. Furthermore, the integration of a graphical user
interface (GUI) provides an intuitive and user-friendly interface for performing
analyses and managing file conversions. Users can interact with MDANSE through
the GUI to directly convert trajectories from different formats to the required
HDF5 format using the Trajectory Converter tool.

.. _text_output:

DAT File Format
-----------------

During an Analysis in MDANSE, the default output format is now `DAT files <https://en.wikipedia.org/wiki/DAT_file>`_, which
are text-based and easily readable. Each DAT file corresponds to a specific
variable generated during the analysis. If the ASCII option is selected, a
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

.. _convert_netcdf:

NetCDF to HDF5 Conversion Script
---------------------------------------

MDANSE now provides a versatile Python script that simplifies the process
of converting existing NetCDF files to the HDF5 format. This script is especially
valuable for users with legacy data stored in NetCDF files who wish to take
advantage of the enhanced capabilities and compatibility offered by MDANSE's
shift to HDF5.

To perform the conversion, follow these steps:

1. Open a terminal or command prompt.
2. Navigate to the directory containing the NetCDF files you want to convert.
3. Run the following command, replacing [input_file.nc] with the name of your
   NetCDF file and [output_file.h5] with your desired name for the resulting
   HDF5 file::

      .. code-block:: bash

         python convert_netcdf_to_hdf5.py [input_file.nc] [output_file.h5]

   This command will execute the conversion script and generate an HDF5 file
   with the specified name.

4. Once the conversion is complete, you can use the newly created HDF5 file
   seamlessly within MDANSE for advanced analysis and visualization.

This convenient script streamlines the migration of existing data to the HDF5
format, ensuring that users can leverage MDANSE's enhanced features while
preserving their valuable data.
