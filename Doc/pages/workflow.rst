
.. _workflow-of-analysis:

MDANSE Workflow
===============

A typical computational workflow for most users
goes through three main stages: (1) trajectory conversion, (2)
analysis calculation and (3) results plotting.

1. Trajectory conversion
------------------------

Before the trajectory can be analysed, it has to be converted
to the MDANSE trajectory format (MDT).
(Please read about MDANSE support for :ref:`note-on-h5md-files`
to find out about possible exceptions from this rule.)

Most likely your trajectory is in whatever format was output
by your preferred Molecular Dynamics simulation software,
and you need to convert it first. The converters will give
you a chance to verify the information about the contents
of the simulated system before you run the conversion.
Once you have converted your trajectory to the MDANSE MDT format,
you can use it as input for all analysis types.
See also :ref:`trajectory-converters`.

2a. Analysis parameters
-----------------------

Most analysis jobs offered by MDANSE are controlled by a number
of input parameters which can be adjusted.
MDANSE GUI typically attempts to fill all the fields with
usable starting values, and highlights the invalid ones
that need to be corrected by the user.
We describe some of the more common parameters found
in MDANSE below.

Frames
^^^^^^

You can decide to limit the range of simulation frames used in the calculations,
or to reduce the number of the frames taken in that
range by increasing the step between them. Only the frames you selected will
be passed to the analysis job. See also :ref:`configurator-analysis-FramesConfigurator`.

A more detailed discussion of the (correlation) frames can be found here:
:ref:`correlation-frames`.

Atom selection
^^^^^^^^^^^^^^

Just as it is not necessary to include all the time frames in the analysis,
it is also possible to select only a subset of all the atoms present in the
trajectory. Once you have defined a selection, you can run an analysis job
on the selected atoms, and ignore the rest. This is useful if you are trying
to determine which atoms contribute to a specific feature in your results.
More details are given in the section :ref:`atom-selection`.

Resolution
^^^^^^^^^^

The resolution is enabled only for the analysis types which calculate an
energy spectrum. This is normally applied to calculations involving
Fourier transform of a correlation function (see also :ref:`correlation-fourier-spectrum`).
The resolution is applied by multiplying
the time-dependent function with a window function before applying the Fourier
transform. The details are given in the section
:ref:`param-instrument-resolution`.

Weighting
^^^^^^^^^

The partial (usually by element) properties calculated can be combined using the weights
chosen by the user, as described in the section :ref:`weighting-scheme`. Please remember
that the MDANSE_GUI normally recommends the weighting scheme appropriate to the
type of analysis performed.

Output files
^^^^^^^^^^^^

All the output arrays created in the analysis are written to the filesystem in the
format chosen by the user. If you intend to continue visualising the results within
the MDANSE_GUI, you will need to use the MDAFormat. If, however, you were planning
to process the results further using other software, then you will need to pick
the TextFormat output. See also :ref:`param-output-files`.

2b. Analysis results
---------------------

The MDA files contain both the results and the original input parameters
used to produce the results. In most cases, the output file will contain
a total result, together with a number of partial datasets.
The partial properties are typically grouped per atom type, or per pair of atom
types. The relative contributions of different atoms to the total results
will depend on the user's choice of weights.

3. Plotting
-----------

If the MDAFormat was chosen for the analysis job output file, the
file can then be opened in the MDANSE_GUI and plotted. As the MDANSE_GUI
plotting is built on the matplotlib library many options found in the
matplotlib are available in MDANSE_GUI. Additionally as the analysis
calculations store unit information with results, MDANSE_GUI
allows users to interactively switch between different units.

More information on plotting can be found in the section
:ref:`plotting-options`.
