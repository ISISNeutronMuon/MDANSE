
.. _workflow-of-analysis:

The MDANSE Workflow
===================

Here we describe a typical computational workflow for most users
which goes through three main stages (1) trajectory conversion, (2)
analysis calculation and (3) results plotting.

1. Trajectory conversion
------------------------
To load a trajectory into MDANSE and run an analysis calculation
the trajectory must be in the MDANSE trajectory format, saved as a HDF file.

Most likely your trajectory is in whatever format was output by your preferred Molecular Dynamics
simulation software, and you need to convert it first. Once you have converted your
trajectory to the MDANSE HDF format, you can use it as input for all kinds of
analysis. See also :ref:`trajectory-converters`

2a. Analysis parameters
-----------------------
Most analysis jobs offered by MDANSE allow a number of different parameters
which can be adjusted. We describe some of the more common parameters found
in MDANSE below.

Frames
^^^^^^
It is not necessary to use all the time frames of your MD simulation. You can decide
to limit the range of simulation time, and reduce the number of the frames taken in that
range by increasing the step between them. Only the frames you selected will
be passed to the analysis job. See also :ref:`param-frames`.

Atom selection
^^^^^^^^^^^^^^
Just as it is not necessary to include all the time frames in the analysis, it is also
possible to select only a subset of all the atoms present in the trajectory. Once you
have defined a selection, you can decide to run an analysis job on the selected atoms, and
ignore the rest. This is useful if you are trying to determine which atoms contribute
to a specific feature in your results. See also :ref:`param-atom-selection`.

Resolution
^^^^^^^^^^
The resolution is enabled only for the analysis types which calculate an energy spectrum.
This is normally applied to calculations involving Fourier transform of a correlation function.
The resolution is applied by multiplying the time-dependent function with a window function
before applying the Fourier transform. The details are given in the section
:ref:`param-instrument-resolution`.

Weighting
^^^^^^^^^
The partial (usually by element) properties calculated can be combined using the weights
chosen by the user, as described in the section :ref:`param-weights`. Please remember
that the MDANSE_GUI normally recommends the weighting scheme appropriate to the
type of analysis performed.

Output files
^^^^^^^^^^^^
All the output arrays created in the analysis are written to the filesystem in the
format chosen by the user. (If you intend to continue visualising the results within
the MDANSE_GUI, you will need to use the HDF5 format. If, however, you were planning
to process the results further using other software, then you will need to pick
the ASCII output. See also :ref:`param-output-files`)

2b. Analysis results
---------------------
The analysis jobs are run in steps, iterating over each part of the trajectory.

The iterations over steps will produce partial results. This is where the specific
equations described in the documentation of an analysis type are applied.
The partial results will be combined into the final result.

The partial properties are calculated, typically per atom type,
or per pair of atom types and are combined into the total result.

3. Plotting
-----------
If the HDF5 format was chosen for the analysis job output file, the
file can then be opened in the MDANSE_GUI and plotted. As the MDANSE_GUI
plotting is built on the matplotlib library many options found in the
matplotlib are available in MDANSE_GUI. Additionally as the analysis
calculations store unit information with results, MDANSE_GUI
allows users to interactively switch between different units.
