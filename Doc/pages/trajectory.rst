
.. _trajectory-converters:

Trajectory Converters
=====================

Converters allow for the
outputs of different MD simulation packages to be used in
MDANSE by converting the various file formats to the MDT format.
An MDT file is meant to contain all the information that is needed
to analyse a trajectory, and so the converters will typically
require the user to add the information that is missing from
the input trajectory. Frequently the time step of the trajectory
has to be specified manually, and in some cases (e.g. LAMMPS)
the information about chemical elements is not guaranteed to
be included in the input files.

Specific converters
~~~~~~~~~~~~~~~~~~~

- ASE (for ASE .traj files)
- CASTEP
- CHARMM
- CP2K
- DCD
- DFTB
- Discover
- DMol
- DL_POLY
- Forcite
- Gromacs
- LAMMPS
- NAMD
- VASP
- XPLOR

General converters
~~~~~~~~~~~~~~~~~~

MDANSE can also use external libraries to read trajectory and structure files.
At the moment, there are three converters which can load different
trajectory formats. If the specific converters listed above do not
work for your input files, please try one of these:

- MDAnalysis
- MDTraj
- ASE
