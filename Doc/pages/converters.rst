.. _converter-list:

List of trajectory converters
=============================


.. _converter-reference-ASE:

ASE
~~~

Converts a trajectory to MDT format using ASE.

Attempts to convert a trajectory file to MDANSE .mdt format (HDF5).
The conversion is done using the ase.io module.
It works both for the ASE's own .traj format, and for other formats
supported by ASE.
Please help the ASE format detection mechanism by using
standard input file names.

Inputs:

- trajectory_file: :ref:`configurator-converter-ASEFileConfigurator` default=INPUT_FILENAME
- atom_aliases: :ref:`configurator-converter-AtomMappingConfigurator` default={}
- time_step: :ref:`configurator-converter-FloatConfigurator` default=1.0
- time_unit: :ref:`configurator-converter-SingleChoiceConfigurator` default=fs
- n_steps: :ref:`configurator-converter-IntegerConfigurator` default=0
- fold: :ref:`configurator-converter-BooleanConfigurator` default=False
- output_files: :ref:`configurator-converter-OutputTrajectoryConfigurator` default=N/A


.. _converter-reference-CASTEP:

CASTEP
~~~~~~

Converts a Castep Trajectory into an MDT trajectory file.

Inputs:

- castep_file: :ref:`configurator-converter-MDFileConfigurator` default=INPUT_FILENAME.md
- atom_aliases: :ref:`configurator-converter-AtomMappingConfigurator` default={}
- fold: :ref:`configurator-converter-BooleanConfigurator` default=False
- output_files: :ref:`configurator-converter-OutputTrajectoryConfigurator` default=N/A


.. _converter-reference-CHARMM:

CHARMM
~~~~~~

Converts a CHARMM trajectory to an MDT trajectory.

Inputs:

- pdb_file: :ref:`configurator-converter-InputFileConfigurator` default=INPUT_FILENAME.pdb
- dcd_file: :ref:`configurator-converter-InputFileConfigurator` default=INPUT_FILENAME.dcd
- time_step: :ref:`configurator-converter-FloatConfigurator` default=1.0
- fold: :ref:`configurator-converter-BooleanConfigurator` default=False
- output_files: :ref:`configurator-converter-OutputTrajectoryConfigurator` default=N/A


.. _converter-reference-CP2K:

CP2K
~~~~

Converts a CP2K trajectory to an MDT trajectory.

Inputs:

- pos_file: :ref:`configurator-converter-XYZFileConfigurator` default=INPUT_FILENAME.xyz
- vel_file: :ref:`configurator-converter-OptionalXYZFileConfigurator` default=
- force_file: :ref:`configurator-converter-OptionalXYZFileConfigurator` default=
- cell_file: :ref:`configurator-converter-InputFileConfigurator` default=INPUT_FILENAME.cell
- atom_aliases: :ref:`configurator-converter-AtomMappingConfigurator` default={}
- fold: :ref:`configurator-converter-BooleanConfigurator` default=False
- output_files: :ref:`configurator-converter-OutputTrajectoryConfigurator` default=N/A


.. _converter-reference-DCD:

DCD
~~~

Converts a DCD trajectory to an MDT trajectory.

Inputs:

- pdb_file: :ref:`configurator-converter-InputFileConfigurator` default=INPUT_FILENAME.pdb
- dcd_file: :ref:`configurator-converter-InputFileConfigurator` default=INPUT_FILENAME.dcd
- time_step: :ref:`configurator-converter-FloatConfigurator` default=1.0
- fold: :ref:`configurator-converter-BooleanConfigurator` default=False
- output_files: :ref:`configurator-converter-OutputTrajectoryConfigurator` default=N/A


.. _converter-reference-DFTB:

DFTB
~~~~

Converts a DFTB trajectory to an MDT trajectory.

Inputs:

- xtd_file: :ref:`configurator-converter-XTDFileConfigurator` default=INPUT_FILENAME.xtd
- trj_file: :ref:`configurator-converter-InputFileConfigurator` default=INPUT_FILENAME.trj
- atom_aliases: :ref:`configurator-converter-AtomMappingConfigurator` default={}
- fold: :ref:`configurator-converter-BooleanConfigurator` default=False
- output_files: :ref:`configurator-converter-OutputTrajectoryConfigurator` default=N/A


.. _converter-reference-DL_POLY:

DL_POLY
~~~~~~~

Converts a DL_POLY trajectory to an MDT trajectory.

Inputs:

- field_file: :ref:`configurator-converter-FieldFileConfigurator` default=INPUT_FILENAME
- history_file: :ref:`configurator-converter-InputFileConfigurator` default=INPUT_FILENAME
- atom_aliases: :ref:`configurator-converter-AtomMappingConfigurator` default={}
- fold: :ref:`configurator-converter-BooleanConfigurator` default=False
- output_files: :ref:`configurator-converter-OutputTrajectoryConfigurator` default=N/A


.. _converter-reference-Forcite:

Forcite
~~~~~~~

Converts a Forcite trajectory to an MDT trajectory.

Inputs:

- xtd_file: :ref:`configurator-converter-XTDFileConfigurator` default=INPUT_FILENAME.xtd
- trj_file: :ref:`configurator-converter-InputFileConfigurator` default=INPUT_FILENAME.trj
- atom_aliases: :ref:`configurator-converter-AtomMappingConfigurator` default={}
- fold: :ref:`configurator-converter-BooleanConfigurator` default=False
- output_files: :ref:`configurator-converter-OutputTrajectoryConfigurator` default=N/A


.. _converter-reference-Gromacs:

Gromacs
~~~~~~~

Converts a Gromacs trajectory to an MDT trajectory.

Inputs:

- pdb_file: :ref:`configurator-converter-InputFileConfigurator` default=INPUT_FILENAME.pdb
- xtc_file: :ref:`configurator-converter-InputFileConfigurator` default=INPUT_FILENAME.xtc
- fold: :ref:`configurator-converter-BooleanConfigurator` default=False
- output_files: :ref:`configurator-converter-OutputTrajectoryConfigurator` default=N/A


.. _converter-reference-LAMMPS:

LAMMPS
~~~~~~

Converts a LAMMPS trajectory to an MDT trajectory.

Inputs:

- config_file: :ref:`configurator-converter-ConfigFileConfigurator` default=INPUT_FILENAME.config
- trajectory_file: :ref:`configurator-converter-InputFileConfigurator` default=INPUT_FILENAME.lammps
- trajectory_format: :ref:`configurator-converter-SingleChoiceConfigurator` default=custom
- lammps_units: :ref:`configurator-converter-SingleChoiceConfigurator` default=real
- atom_type: :ref:`configurator-converter-SingleChoiceConfigurator` default=From config
- atom_aliases: :ref:`configurator-converter-AtomMappingConfigurator` default={}
- time_step: :ref:`configurator-converter-FloatConfigurator` default=1.0
- n_steps: :ref:`configurator-converter-IntegerConfigurator` default=0
- fold: :ref:`configurator-converter-BooleanConfigurator` default=False
- output_files: :ref:`configurator-converter-OutputTrajectoryConfigurator` default=N/A


.. _converter-reference-MDAnalysis:

MDAnalysis
~~~~~~~~~~

Converts a trajectory to the MDT format using MDAnalysis.

MDAnalysis reads MD trajectories by specifying
topology and coordinate files. Multiple files can be used for the
coordinate files so that trajectories will be stitched together.
For supported file formats, the continuous option ensures that
duplicated time-frames will not be added, see
<a href="https://userguide.mdanalysis.org/stable/reading_and_writing.html">reading and writing</a>.
For topology and coordinate files supported by MDAnalysis see
<a href="https://userguide.mdanalysis.org/stable/formats/index.html#formats">formats</a>.

Inputs:

- topology_file: :ref:`configurator-converter-MDAnalysisTopologyFileConfigurator` default=INPUT_FILENAME
- coordinate_files: :ref:`configurator-converter-MDAnalysisCoordinateFileConfigurator` default=
- atom_aliases: :ref:`configurator-converter-AtomMappingConfigurator` default={}
- time_step: :ref:`configurator-converter-MDAnalysisTimeStepConfigurator` default=0.0
- fold: :ref:`configurator-converter-BooleanConfigurator` default=False
- continuous: :ref:`configurator-converter-BooleanConfigurator` default=False
- output_files: :ref:`configurator-converter-OutputTrajectoryConfigurator` default=N/A


.. _converter-reference-MDTraj:

MDTraj
~~~~~~

Converts a trajectory to the MDT format using MDTraj.

MDTraj reads MD trajectories by specifying trajectory files and optionally
a topology file. Multiple files can be used for the trajectory files so that
trajectories will be stitched together.

Inputs:

- coordinate_files: :ref:`configurator-converter-MDTrajTrajectoryFileConfigurator` default=["INPUT_FILENAME"]
- topology_file: :ref:`configurator-converter-MDTrajTopologyFileConfigurator` default=
- atom_aliases: :ref:`configurator-converter-AtomMappingConfigurator` default={}
- time_step: :ref:`configurator-converter-MDTrajTimeStepConfigurator` default=0.0
- fold: :ref:`configurator-converter-BooleanConfigurator` default=False
- discard_overlapping_frames: :ref:`configurator-converter-BooleanConfigurator` default=False
- output_files: :ref:`configurator-converter-OutputTrajectoryConfigurator` default=N/A


.. _converter-reference-NAMD:

NAMD
~~~~

Converts a NAMD trajectory to an MDT trajectory.

Inputs:

- pdb_file: :ref:`configurator-converter-InputFileConfigurator` default=INPUT_FILENAME.pdb
- dcd_file: :ref:`configurator-converter-InputFileConfigurator` default=INPUT_FILENAME.dcd
- time_step: :ref:`configurator-converter-FloatConfigurator` default=1.0
- fold: :ref:`configurator-converter-BooleanConfigurator` default=False
- output_files: :ref:`configurator-converter-OutputTrajectoryConfigurator` default=N/A


.. _converter-reference-VASP:

VASP
~~~~

Converts a VASP XDATCAR file to an MDT trajectory.

This converter works for XDATCAR files which contain a *header*
specifying the unit cell size and atom types.

If your XDATCAR file does not have a header, you can add it manually
to the beginning of the file. The header can be copied from
the CONTCAR file.

A valid header should look like this:

.. code-block::

    unknown system
    1
    9.050041    0.000000    0.000000
    0.000000    8.236754    0.000000
    0.000000    0.000000   11.000452
    Cu   Rb   Cl    S
    9   4   7   12

where the last two lines specify the atomic types and the number
of the atoms of each type in the same order as they appear in the
atom coordinates below.

Inputs:

- xdatcar_file: :ref:`configurator-converter-XDATCARFileConfigurator` default=INPUT_FILENAME
- atom_aliases: :ref:`configurator-converter-AtomMappingConfigurator` default={}
- time_step: :ref:`configurator-converter-FloatConfigurator` default=1.0
- fold: :ref:`configurator-converter-BooleanConfigurator` default=False
- output_files: :ref:`configurator-converter-OutputTrajectoryConfigurator` default=N/A


.. _converter-reference-XPLOR:

XPLOR
~~~~~

Converts an Xplor trajectory to an MDT trajectory.

Inputs:

- pdb_file: :ref:`configurator-converter-InputFileConfigurator` default=INPUT_FILENAME.pdb
- dcd_file: :ref:`configurator-converter-InputFileConfigurator` default=INPUT_FILENAME.dcd
- time_step: :ref:`configurator-converter-FloatConfigurator` default=1.0
- fold: :ref:`configurator-converter-BooleanConfigurator` default=False
- output_files: :ref:`configurator-converter-OutputTrajectoryConfigurator` default=N/A

