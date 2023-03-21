

Workflow
========

Most analysis jobs offered by MDANSE follow the same pattern of execution:

Input
-----

Trajectory
^^^^^^^^^^

The trajectory must be in the MDANSE format, saved as a NetCDF file.

(Most likely
your trajectory is in whatever format was output by your preferred Molecular Dynamics
simulation software, and you need to convert it first. Once you have converted your
trajectory to the MDANSE NetCDF format, you can use it as input for all kinds of
analysis.)

Frames
^^^^^^

It is not necessary to use all the time frames of your MD simulation. You can decide
to limit the range of simluation time, and reduce the number of the frames taken in that
range by increasing the step between them. Only the frames you selected will
be passed to the analysis.

Atom selection
^^^^^^^^^^^^^^

Just as it is not necessary to include all the time frames in the analysis, it is also
possible to select only a subset of all the atoms present in the trajectory. Once you
have defined a selection, you can decide to run an analysis on the selected atoms, and
ignore the rest. This is useful if you are trying to determine which atoms contribute
to a specific feature in your signal.

Analysis
--------

The analysis is run in steps, iterating over parts of the trajectory.

If you chose to
determine the atom velocities by interpolation, it will be done at this stage.

The iterations over steps will produce partial results, which can be combined into
the final result in the next step of the workflow.

Finalising
----------

At this stage the partial properties have been calculated, typically per atom type,
or per pair of atom types. They will now be combined into the final result.

Resolution
^^^^^^^^^^

If the analysis allows for applying instrumental resolution, it will be done first.
The resolution is enabled only for the analysis types which calculate an energy spectrum.
This is normally done by calculating a Fourier transform of a correlation function.
The resolution is applied by multiplying the correlation function by a window function
before applying the Fourier transform

:ref:`param-instrument-resolution`