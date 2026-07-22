
.. _full_parameter_list:

Input Parameter Types
=====================

Converter Inputs
~~~~~~~~~~~~~~~~

.. _configurator-converter-AtomMappingConfigurator:

AtomMappingConfigurator
-----------------------

default={}

The atom mapping configurator for trajectory converters.

It allows the user to verify and potentially change the way
atom types from an MD trajectory will be converted to the
chemical elements used by MDANSE.

Attributes
----------
_default : dict
The default atom map setting JSON string.



.. _configurator-converter-BooleanConfigurator:

BooleanConfigurator
-------------------

default=False

Sets a value to a logical True or False.

The input value can be directly provided as a Python boolean
or by the using the following (standard)
representation of a boolean: 'true'/'false', 'yes'/'no', 'y'/'n', '1'/'0', 1/0


.. _configurator-converter-FileWithAtomDataConfigurator:

FileWithAtomDataConfigurator
----------------------------

default=


Class for handling files that contain atom information.

Returns the parsed structure in the ``instance`` attribute.

If this is ``optional`` and undefined, ``instance`` will instead be
``None`` for easy checking.

Parameters
----------
parser : type[Parser] or Callable
Routine or object to parse data into relevant form.

Notes
-----
For old behaviour any object subclassing this can pass ``self.parse`` into the
``parser`` argument.


.. _configurator-converter-FloatConfigurator:

FloatConfigurator
-----------------

default=0

Inputs a single floating-point number.

.. _configurator-converter-InputFileConfigurator:

InputFileConfigurator
---------------------

default=

Uses a file as input. Very general.

.. _configurator-converter-IntegerConfigurator:

IntegerConfigurator
-------------------

default=0

Inputs a single integer number.

.. _configurator-converter-MDAnalysisCoordinateFileConfigurator:

MDAnalysisCoordinateFileConfigurator
------------------------------------

default=('', 'AUTO')

Take one or more filenames of files containing atomic coordinates.

Several trajectory files can be concatenated using this input,
but only if they are all in the same format.


.. _configurator-converter-MDAnalysisTimeStepConfigurator:

MDAnalysisTimeStepConfigurator
------------------------------

default=0.0

Input for the trajectory time step in the MDAnalysis converter.

MDAnalysis will attempt to determine the correct value of the time step
based on the input files. That value is not guaranteed to be correct.


.. _configurator-converter-MDAnalysisTopologyFileConfigurator:

MDAnalysisTopologyFileConfigurator
----------------------------------

default=('', 'AUTO')

Constructs and MDAnalysis.Universe from the input file.

The format of the input file can be specified manually, or
set to AUTO. The automatic format determination typically
fails for filenames without an extension.


.. _configurator-converter-MDTrajTimeStepConfigurator:

MDTrajTimeStepConfigurator
--------------------------

default=0.0

Inputs the time step value for the MDTraj converter.

.. _configurator-converter-MDTrajTopologyFileConfigurator:

MDTrajTopologyFileConfigurator
------------------------------

default=

Uses MDTraj to read the system topology information from a file.

.. _configurator-converter-MDTrajTrajectoryFileConfigurator:

MDTrajTrajectoryFileConfigurator
--------------------------------

default=

Passes one or more trajectory files to the MDTraj converter.

Multiple files can be concatenated, but they have to be all in
the same format.


.. _configurator-converter-OutputTrajectoryConfigurator:

OutputTrajectoryConfigurator
----------------------------

default=('OUTPUT_TRAJECTORY', 64, 128, 'none', 'no logs')

Specifies how a trajectory should be output to a file.

Allows to define:

- path to the file,
- precision of the floating point numbers,
- HDF5 chunk size,
- compression applied to the HDF5 datasets
- logging level of the converter run.

For trajectories, MDANSE supports only the MDT format (HDF5).


.. _configurator-converter-SingleChoiceConfigurator:

SingleChoiceConfigurator
------------------------

default=[]

Selects a single item from multiple choices.

Analysis Inputs
~~~~~~~~~~~~~~~

.. _configurator-analysis-AtomSelectionConfigurator:

AtomSelectionConfigurator
-------------------------
.. code-block:: Python

  default={
           "0": {"function_name": "select_all", "operation_type": "union"},
           "1": {"function_name": "select_dummy", "operation_type": "difference"}
          }

Selects atoms in trajectory based on the input string.

This configurator allows the selection of a specific set of
atoms on which the analysis will be performed. The default setting
selects all atoms.

Attributes
----------
_default : str

The default selection setting.



.. _configurator-analysis-AtomTransmutationConfigurator:

AtomTransmutationConfigurator
-----------------------------

default={}

Assigns different chemical elements to selected atoms.

For some analysis it can be necessary to change the nature of the
chemical element of a given part of the system to have results
closer to experience. A good example is to change some hydrogen
atoms to deuterium in order to fit with experiments where
deuteration experiments have been performed for improving the
contrast and having a better access to the dynamics of a specific
part of the molecular system.

Attributes
----------
_default : str
The default transmutation setting.



.. _configurator-analysis-AxisSelectionConfigurator:

AxisSelectionConfigurator
-------------------------

default=(None, 0)

Defines a local axis in a molecule.

The input is the name of a molecule type, and one or two indices
of atoms within the molecule.

If the atom indices are not defined, the calculation will use
the principal axis of the molecule determined from the moment
of inertia.

If one index is given, the molecule axis will be a vector from
the molecule centre to the atom with the given index.

If two indices are given, the molecule axis will be a vector
between the atoms with the two indices.


.. _configurator-analysis-BooleanConfigurator:

BooleanConfigurator
-------------------

default=False

Sets a value to a logical True or False.

The input value can be directly provided as a Python boolean
or by the using the following (standard)
representation of a boolean: 'true'/'false', 'yes'/'no', 'y'/'n', '1'/'0', 1/0


.. _configurator-analysis-CorrelationFramesConfigurator:

CorrelationFramesConfigurator
-----------------------------

default=all

Parses the input of trajectory frames.

Configures the time frame range to be used in the calculations
together with a movable window used for correlations.


.. _configurator-analysis-DerivativeOrderConfigurator:

DerivativeOrderConfigurator
---------------------------

default=3

Specifies the order of a numerical derivative.

Values from 1 to 5 are allowed.


.. _configurator-analysis-DistHistCutoffConfigurator:

DistHistCutoffConfigurator
--------------------------

default=(0, 10, 1)

Range of interatomic distances for a histogram.

It does not allow distances large enough to include
the periodic image of any atom in the system.


.. _configurator-analysis-FloatConfigurator:

FloatConfigurator
-----------------

default=0

Inputs a single floating-point number.

.. _configurator-analysis-FramesConfigurator:

FramesConfigurator
------------------

default=all

Select the trajectory frames on which to run the analysis.

The frame selection can be input as three numbers, in the format
of (first, last, step).


.. _configurator-analysis-GridStepConfigurator:

GridStepConfigurator
--------------------

default=0

Configurator to manage a finite element grid within the unit cell.

This configurator provides extra information about a grid in a
trajectory's unit cell.

It can also read a primary cell-vector along which the spacing is defined
which is specified in the optional `axis` dependency
(an :class:`AxisSelectionConfigurator` instance).

If any frame does not have a unit cell, the maximum span of the atoms is
used, otherwise the average unit cell is used.

The input value specifies the grid spacing in `nm`.

If `axis` is present, information about the prediction is stored in `grid`
and is a single range along the primary axis.

If `axis` is not present, information about the prediction is stored in the keys:

- `a-direction grid`
- `b-direction grid`
- `c-direction grid`


.. _configurator-analysis-GroupingLevelConfigurator:

GroupingLevelConfigurator
-------------------------

default=atom

Define how the partial results will be grouped in the output.

The grouping levels currently supported are:
    * 'atom': no changes are made to the atom selection
    * 'molecule': this changes the atom names in the atom selection so
      that it includes the molecule name that they are a part of e.g.
      <H2_O1>/H for a water molecule's hydrogen atom. Job in mdanse will
      sum results based on the atom names so that results like
      f(q,t)/<H2_O1>/H will be obtained.


.. _configurator-analysis-HDFInputFileConfigurator:

HDFInputFileConfigurator
------------------------

default=INPUT_FILENAME.mda

Uses an .mda file from another analysis as input.

.. _configurator-analysis-HDFTrajectoryConfigurator:

HDFTrajectoryConfigurator
-------------------------

default=INPUT_FILENAME.mdt

Chooses the trajectory to be analysed.

You can use it both with an .mdt file created by an MDANSE converter,
or with an H5MD file if it contains complete information about the
atom positions, time axis, physical units and atom types.


.. _configurator-analysis-InstrumentResolutionConfigurator:

InstrumentResolutionConfigurator
--------------------------------

default=('gaussian', {'mu': 0.0, 'sigma': 10.0})

Defines the resolution function to use for signal broadening.

The instrument resolution will be used in frequency-dependent analysis
(e.g. the vibrational density of states) when performing the Fourier
transform of its time-dependent counterpart. The convolution of the signal
with a resolution function should be closer to the experimental spectrum.

In MDANSE, the instrument resolution is calculated as a function of energy,
and then Fourier-transformed into the time domain and applied to the
time-dependent signal as follows:

.. math:: FT(f(t)r(t)) = F(\omega) * R(\omega) = G(\omega)

where f(t) and r(t) are, respectively, the time-dependent signal and
instrument resolution. :math:`F(\omega)` and :math:`R(\omega)`
are their corresponding spectra. Hence, :math:`G(\omega)` represents
the convolution of the signal and the instrument resolution. This resolution
is constant and not energy-dependent, as opposed to the real resolution
of most neutron instruments.



.. _configurator-analysis-IntegerConfigurator:

IntegerConfigurator
-------------------

default=0

Inputs a single integer number.

.. _configurator-analysis-InterpolationOrderConfigurator:

InterpolationOrderConfigurator
------------------------------

default=3

Specifies the order of a numerical derivative used for interpolation.

Normally it is used for calculating atom velocities from their positions.
Values from 1 to 5 are allowed. If MD engine velocities are provided in the
trajectory file, you can (and should) choose to use them by setting this to 0.

The velocities calculated from atom positions may differ from the values used
by the MD engine during the simulation. Additionally, if your MD engine was
not writing out every frame, the velocities are likely to be
underestimated compared to the values used by the MD engine in the simulation,
and the error in the calculation increases quickly with the number of trajectory
frames skipped in the MD output.



.. _configurator-analysis-MoleculeSelectionConfigurator:

MoleculeSelectionConfigurator
-----------------------------

default=

Picks a molecule type present in the trajectory.

If the molecule labels are not available, you can detect the molecules
using TrajectoryEditor.

Attributes
----------
_default : str
Empty by default.



.. _configurator-analysis-OptionalFloatConfigurator:

OptionalFloatConfigurator
-------------------------

default=[False, 1.0]

Inputs a single floating point number. Empty input is allowed.

.. _configurator-analysis-OutputFilesConfigurator:

OutputFilesConfigurator
-----------------------

default=('OUTPUT_FILENAME', ['MDAFormat', 'TextFormat', 'FileInMemory'], 'no logs')

Allows the user to choose the output file for writing.

This configurator allows to define:

- output directory and the base file name,
- format(s) of the output file(s),
- logging level of the analysis run.

The list of output files is built by joining the given output directory, the
base file name and the extensions corresponding to the input file formats.

For analysis, MDANSE currently supports:

1. MDAFormat - an HDF5 file written to the disk,
2. TextFormat - a tar file containing a text file for each array,
3. FileInMemory - an HDF5 data object NOT written to the disk.

FileInMemory is not available when running from the GUI.


.. _configurator-analysis-OutputStructureConfigurator:

OutputStructureConfigurator
---------------------------

default=('OUTPUT_FILENAME', 'vasp', 'no logs')

Defines the name of the output (average) structure file.

Allows to define:

- output directory and file name,
- output structure file format (supported by ASE io module),
- logging level of the analysis run.



.. _configurator-analysis-OutputTrajectoryConfigurator:

OutputTrajectoryConfigurator
----------------------------

default=('OUTPUT_TRAJECTORY', 64, 128, 'none', 'no logs')

Specifies how a trajectory should be output to a file.

Allows to define:

- path to the file,
- precision of the floating point numbers,
- HDF5 chunk size,
- compression applied to the HDF5 datasets
- logging level of the converter run.

For trajectories, MDANSE supports only the MDT format (HDF5).


.. _configurator-analysis-PartialChargeConfigurator:

PartialChargeConfigurator
-------------------------

default={}

Assigns partial charges to atoms.

.. _configurator-analysis-ProjectionConfigurator:

ProjectionConfigurator
----------------------

default=None

Projects atomic coordinates onto an axis or plane.

Null projector (which does nothing) is the standard choice.
The input vector can be used as an axis direction,
or as a plane normal vector.



.. _configurator-analysis-QRangeConfigurator:

QRangeConfigurator
------------------

default=(0, 10, 1)

Range configurator for Q vector generation.

.. _configurator-analysis-QVectorsConfigurator:

QVectorsConfigurator
--------------------

default=('SphericalLatticeQVectors', {'shells': (0.0, 5.0, 1.0), 'width': 1.0, 'n_samples': 100000, 'n_vectors': 1000, 'seed': 0, 'force_equal_weights': False})

Creates and configures a q-vector generator.

Reciprocal vectors are used in MDANSE for analysis related to
scattering experiments, such as dynamic coherent structure
or elastic incoherent structure factor analysis. In MDANSE, properties
that depend on Q vectors are always scalar regarding Q vectors
in the sense that the values of these properties will be computed
for a given norm of Q vectors and not for a given Q vector.
Hence, the Q vectors generator supported by MDANSE always generates
Q vectors on Q-shells, each shell containing a set of Q vectors whose
norm match the Q shell value within a given tolerance.

Depending on the generator selected, Q vectors can be generated
isotropically or anisotropically, on a lattice or randomly.



.. _configurator-analysis-RangeConfigurator:

RangeConfigurator
-----------------

default=(0, 10, 1)

Inputs a range of values as 3 parameters : start, stop, step.

By default the values are generated as a NumPy array.


.. _configurator-analysis-RunningModeConfigurator:

RunningModeConfigurator
-----------------------

default=('single-core', 1)

Specifies how many CPU cores will be used by this task.

MDANSE currently support single-core or multicore (SMP) running modes.
In the latter case, you have to specify the number of slots used for
running the analysis.


.. _configurator-analysis-SingleChoiceConfigurator:

SingleChoiceConfigurator
------------------------

default=[]

Selects a single item from multiple choices.

.. _configurator-analysis-TrajectoryFilterConfigurator:

TrajectoryFilterConfigurator
----------------------------

default={"filter": "Butterworth", "attributes": {"order": 1, "attenuation_type": "lowpass", "cutoff_freq": 0.0001}}

Defines the filter that will be applied to atom positions.

The filters are provided by the scipy.signal library.

Attributes
----------
_default : str
The default selection setting.



.. _configurator-analysis-UnitCellConfigurator:

UnitCellConfigurator
--------------------

default=([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]], False)

Input a unit cell definition.

This is normally used to introduce a cell definition to a trajectory,
or to change the existing cell definition.


.. _configurator-analysis-VectorConfigurator:

VectorConfigurator
------------------

default=[1.0, 0.0, 0.0]

Inputs a vector given as 3 floating point numbers.

.. _configurator-analysis-WeightsConfigurator:

WeightsConfigurator
-------------------

default=equal

Select the atom property to be used by the weight scheme.

This configurator allows to select which atom properties will be used as weights
when combining the partial contributions into the total result.


