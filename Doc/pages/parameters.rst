
.. _parameters:

Glossary of Parameters
=======================

Analysis Parameters
~~~~~~~~~~~~~~~~~~~

**AtomSelectionConfigurator**
-----------------------------

  default={}

    Selects atoms in trajectory based on the input string.

    This configurator allows the selection of a specific set of
    atoms on which the analysis will be performed. The defaults setting
    selects all atoms.

    Attributes
    ----------
    _default : str
        The defaults selection setting.

    

**AtomTransmutationConfigurator**
---------------------------------

  default={}

    This configurator allows to define a set of atoms to be
    transmuted to a given chemical element.

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
        The defaults transmutation setting.
    

**AtomsListConfigurator**
-------------------------

  default=None

    
    This configurator allows of a given list of atom names.

    The atoms has to belong to the same molecule.

    :note: this configurator depends on 'trajectory'
    

**AxisSelectionConfigurator**
-----------------------------

  default=None

    
    This configurator allows to define a local axis per molecule.

    For each molecule, the axis is defined using the coordinates of two atoms of the molecule.

    :note: this configurator depends on 'trajectory' configurator to be configured.
    

**BasisSelectionConfigurator**
------------------------------

  default=None

    
    This configurator allows to define a local basis per molecule.

    For each molecule, the basis is defined using the coordinates of three atoms of the molecule.
    These coordinates will respectively define the origin, the X axis and y axis of the basis, the
    Z axis being latter defined in such a way that the basis is direct.
    

**BooleanConfigurator**
-----------------------

  default=False

    
    This Configurator allows to input a Boolean Value (True or False).

    The input value can be directly provided as a Python boolean or by the using the following (standard)
     representation of a boolean: 'true'/'false', 'yes'/'no', 'y'/'n', '1'/'0', 1/0
    



**CorrelationFramesConfigurator**
---------------------------------

  default=all

    Parses the input of trajectory frames.

    Configures the time frame range to be used in the calculations
    together with a movable window used for correlations.
    

**DerivativeOrderConfigurator**
-------------------------------

  default=3

    Configurator used when numerical derivatives are required.

**DistHistCutoffConfigurator**
------------------------------

  default=(0, 10, 1)

    None


**FloatConfigurator**
---------------------

  default=0

    
    This Configurator allows to input a float.
    

**FramesConfigurator**
----------------------

  default=all

    
    This configurator allows to input a frame selection for the analysis.

    The frame selection can be input as:

    #. a 3-tuple where the 1st, 2nd will correspond respectively to the indices of the first and     last (excluded) frames to be selected while the 3rd element will correspond to the step number between two frames. For example (1,11,3) will give 1,4,7,10
    #. *'all'* keyword, in such case, all the frames of the trajectory are selected
    #. ``None`` keyword, in such case, all the frames of the trajectory are selected

    :note: this configurator depends on 'trajectory' configurator to be configured
    

**GroupingLevelConfigurator**
-----------------------------

  default=atom

    
    This configurator allows to choose the level of granularity in the atom selection.

    When reading the trajectory, the level of granularity will be applied by grouping the atoms of the selection
    to a single dummy-atoms located on the center of gravity of those atoms.

    The level of granularity currently supported are:

    * 'atom': no grouping will be performed
    * 'group': the atoms that belongs to an AtomCluster object will be grouped as a single atom per object while the ones that belongs to a Molecule, NucleotideChain, PeptideChain and Protein object will be grouped according to the chemical group they belong to (e.g. peptide group, methyl group ...)
    * 'residue': the atoms that belongs to anAtomCluster or Molecule object will be grouped as a single atom per object while the ones thta belongs to a NucleotideChain, PeptideChain or Protein object will be grouped according to the residue to which they belong to (e.g. Histidine, Cytosyl ...)
    * 'chain': the atoms that belongs to an AtomCluster or Molecule object will be grouped as a single atom per object while the ones that belongs to a NucleotideChain, PeptideChain or Protein object will be grouped according to the chain they belong to
    * 'molecule': the atoms that belongs to any chemical entity will be grouped as a single atom per object
    

**HDFInputFileConfigurator**
----------------------------

  default=INPUT_FILENAME.mda

    
    This configurator allows to input an HDF file as input file.
    

**HDFTrajectoryConfigurator**
-----------------------------

  default=INPUT_FILENAME.mdt

    
    This configurator allow to input a HDF trajectory file.

    HDF trajectory file is the format used in MDANSE to store Molecular Dynamics trajectories. It is an HDF5 file
    that store various data related to the molecular dynamics : atomic positions, velocities, energies, energy gradients etc...

    To use trajectories derived from MD packages different from HDF, it is compulsory to convert them before to a
    HDF trajectory file.

    :attention: once configured, the HDF trajectory file will be opened for reading.
    

**InputDirectoryConfigurator**
------------------------------

  default=MDANSE/Tests/UnitTests

    
    This Configurator allows to set an input directory.

    :attention: The directory will be created at configuration time if it does not exist.
    

**InputFileConfigurator**
-------------------------

  default=

    
    This Configurator allows to set an input file.
    

**InstrumentResolutionConfigurator**
------------------------------------

  default=('gaussian', {'mu': 0.0, 'sigma': 10.0})

    
    This configurator allows to set an instrument resolution.

    The instrument resolution will be used in frequency-dependant analysis (e.g. the vibrational density
    of states) when performing the fourier transform of its time-dependant counterpart. This allow to
    convolute of the signal with a resolution function to have a better match with experimental spectrum.

    In MDANSE, the instrument resolution are defined in omegas space and are internally
    inverse-fourier-transformed to get a time-dependant version. This time-dependant resolution function will then
    be multiplied by the time-dependant signal to get the resolution effect according to the Fourier Transform theorem:

    .. math:: TF(f(t) * r(t)) = F(\omega) \otimes R(\omega) = G(\omega)

    where f(t) and r(t) are respectively the time-dependant signal and instrument resolution and
    F(\omega) and R(\omega) are their corresponding spectrum. Hence, G(\omega) represents the signal
    convoluted by the instrument resolution and, as such, represents the quantity to be compared directly with
    experimental results.

    An instrument resolution is represented in MDANSE by a kernel function and a sets of parameters for this function.
    MDANSE currently supports the aussian, lorentzian, square, triangular and pseudo-voigt kernels.

    :note: this configurator depends on the 'frame' configurator to be configured.
    

**IntegerConfigurator**
-----------------------

  default=0

    
    This Configurator allows to input an integer.
    

**InterpolationOrderConfigurator**
----------------------------------

  default=3

    
    This configurator allows to input the interpolation order to be applied when deriving velocities from atomic coordinates.

    The allowed value are 0 (no interpolation) , 1 (1st order), ..., 5 (5th order), the
    former one will not interpolate the velocities from atomic coordinates but will directly use the velocities stored in the trajectory file.

    :attention: it is of paramount importance for the trajectory to be sampled with a very low time     step to get accurate velocities interpolated from atomic coordinates.

    :note: this configurator depends on 'trajectory' configurator to be configured.
    

**McStasInstrumentConfigurator**
--------------------------------

  default=

    
    This configurator allows to input a McStas executable file
    

**McStasOptionsConfigurator**
-----------------------------

  default={'ncount': 10000, 'dir': PosixPath('/var/folders/jx/__bc7gns12g9b7f_v09x8mzm0000gq/T/mcstas_output/05.06.2025-11:53:42')}

    
    This configurator allows to input the McStas options that will be used to run a McStas executable file.
    

**McStasParametersConfigurator**
--------------------------------

  default={'beam_wavelength_Angs': 2.0, 'environment_thickness_m': 0.002, 'beam_resolution_meV': 0.1, 'container': 'INPUT_FILENAME.laz', 'container_thickness_m': 5e-05, 'sample_height_m': 0.05, 'environment': 'INPUT_FILENAME.laz', 'environment_radius_m': 0.025, 'sample_thickness_m': 0.001, 'sample_detector_distance_m': 4.0, 'sample_width_m': 0.02, 'sample_rotation_deg': 45.0, 'detector_height_m': 3.0}

    
    This configurator allows to input the McStas instrument parameters that will be used to run a McStas executable file.
    

**MockTrajectoryConfigurator**
------------------------------

  default=None

    
    This is a replacement for a trajectory stored in and HDF5 file.
    It is intended to be a drop-in replacement for HDFTrajectoryConfigurator,
    even though it is NOT based on an HDF5 file.
    It can use a JSON file with MockTrajectory parameters to create
    a trajectory entirely in the RAM.
    

**MoleculeSelectionConfigurator**
---------------------------------

  default=

    Picks a molecule type present in the trajectory.

    Attributes
    ----------
    _default : str
        Empty by default.


**MultipleChoicesConfigurator**
-------------------------------

  default=[]

    
    This Configurator allows to select several items among multiple choices.

    :attention: all the selected items must belong to the allowed selection list.
    

**OptionalFloatConfigurator**
-----------------------------

  default=[False, 1.0]

    
    This Configurator allows to input a float.
    

**OutputDirectoryConfigurator**
-------------------------------

  default=MDANSE/Tests/UnitTests

    
    This Configurator allows to set an output directory.
    

**OutputFilesConfigurator**
---------------------------

  default=('OUTPUT_FILENAME', ['MDAFormat', 'TextFormat', 'FileInMemory'], 'no logs')

    Allows the user to choose the output file for writing.

    This configurator allows to define the output directory,
    the basename, and the format(s) of the output file(s)
    resulting from an analysis.

    Once configured, this configurator will provide a list of files
    built by joining the given output directory, the
    basename and the extensions corresponding to the input file formats.

    For analysis, MDANSE currently supports:
    1. MDAFormat - an HDF5 file written to the disk,
    2. TextFormat - a tar file containing a text file for each array,
    3. FileInMemory - an HDF5 data object NOT written to the disk.
    FileInMemory is not available when running from the GUI.
    To define a new output file format for an analysis, you must inherit
    from MDANSE.Framework.Formats.IFormat.IFormat interface.
    

**OutputStructureConfigurator**
-------------------------------

  default=('OUTPUT_FILENAME', 'vasp')

    
    This configurator allows to define the output directory, the basename, and the format(s) of the output file(s)
    resulting from an analysis.

    Once configured, this configurator will provide a list of files built by joining the given output directory, the
    basename and the extensions corresponding to the input file formats.

    For analysis, MDANSE currently supports only the HDF and Text formats. To define a new output file format
    for an analysis, you must inherit from MDANSE.Framework.Formats.IFormat.IFormat interface.


**PartialChargeConfigurator**
-----------------------------

  default={}

    This configurator allows to input partial charges.

**ProjectionConfigurator**
--------------------------

  default=None

    
    This configurator allows to define a projector for atomic coordinates.

    Planar and axial projections are supported by MDANSE while a null projector, that does not project the coordinates, has been introduced
    in MDANSE.Framework.Projectors.IProjector.IProjector for the sake of homogeneity.
    

**PythonObjectConfigurator**
----------------------------

  default=""

    
    This Configurator allows to input and evaluate basic python object.

    The python object supported are strings, numbers, tuples, lists, dicts, booleans and None type.

    :note: this configurator is based on a literal and safe evaluation of the input using ast standard library module.
    

**PythonScriptConfigurator**
----------------------------

  default=

    
    This configurator allows to input a Python script.
    

**QVectorsConfigurator**
------------------------

  default=('SphericalLatticeQVectors', {'shells': (0.1, 5, 0.1), 'width': 0.1, 'n_vectors': 50, 'seed': 0})

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
    isotropically or anistropically, on a lattice or randomly.

    

**RangeConfigurator**
---------------------

  default=(0, 10, 1)

    
    This configurator allow to input a range of values given 3 parameters : start, stop, step.

    By default the values are generated as a NumPy array.
    

**RunningModeConfigurator**
---------------------------

  default=('single-core', 1)

    
    This configurator allows to choose the mode used to run the calculation.

    MDANSE currently support single-core or multicore (SMP) running modes. In the latter case, you have to
    specify the number of slots used for running the analysis.
    

**SingleChoiceConfigurator**
----------------------------

  default=[]

    
    This Configurator allows to select a single item among multiple choices.
    

**SingleOutputFileConfigurator**
--------------------------------

  default=('OUTPUT_FILENAME', 'HDFFormat')

    
    This configurator allows to define the output directory, the basename, and the format(s) of the output file(s)
    resulting from a trajectory conversion.

    Once configured, this configurator will provide a list of files built by joining the given output directory,
    the basename and the  extensions corresponding to the input file formats.

    For trajectories, MDANSE supports only the HDF format. To define a new output file format for a trajectory
    conversion, you must inherit from the MDANSE.Framework.Formats.IFormat.IFormat interface.
    

**StringConfigurator**
----------------------

  default=

    
    This Configurator allows to input a string.
    

**TrajectoryVariableConfigurator**
----------------------------------

  default=velocities

    
    This configurator allows to check that a given variable is actually present in a configuration.

    :note: this configurator depends on 'trajectory' configurator to be configured
    

**UnitCellConfigurator**
------------------------

  default=([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]], False)

    
    This configurator allows to input a unit cell, in order to replace
    or change the existing cell definition
    

**VectorConfigurator**
----------------------

  default=[1.0, 0.0, 0.0]

    
    This configurator allows to input a 3D vector, by giving its 3 components
    

**WeightsConfigurator**
-----------------------

  default=equal

    
    This configurator allows to select how the properties that depends on atom type will be weighted when computing
    the total contribution of all atoms.

    Any numeric property defined in MDANSE.Data.ElementsDatabase.ElementsDatabase can be used as a weigh.
    
   
Converter Inputs
~~~~~~~~~~~~~~~~

**ASEFileConfigurator**
-----------------------

  default=

    
    This Configurator allows to set an input file.
    

**AseInputFileConfigurator**
----------------------------

  default=

    
    This Configurator allows to set an input file.
 
**AtomMappingConfigurator**
---------------------------

  default={}

    The atom mapping configurator.

    Attributes
    ----------
    _default : dict
        The default atom map setting JSON string.

**ConfigFileConfigurator**
--------------------------

  default=

    Parse the result of a LAMMPS ``write_data``.

    Provides necessary initial details if not included in
    trajectory.
    
**FieldFileConfigurator**
-------------------------

  default=

    The DL_POLY field file configurator.

**FileWithAtomDataConfigurator**
--------------------------------

  default=

    None


**MDAnalysisCoordinateFileConfigurator**
----------------------------------------

  default=('', 'AUTO')

    None

**MDAnalysisTimeStepConfigurator**
----------------------------------

  default=0.0

    None

**MDAnalysisTopologyFileConfigurator**
--------------------------------------

  default=('', 'AUTO')

    None

**MDFileConfigurator**
----------------------

  default=

    
    Class representing a .md file format (documentation can be found at
    https://www.tcm.phy.cam.ac.uk/castep/MD/node13.html). It is used to determine the structure of the file (eg. the
    length of each section) and to read the information stored in one frame of the trajectory.
    

**MDMCTrajectoryConfigurator**
------------------------------

  default=None

    
    This is a replacement for a trajectory stored in and HDF5 file.
    It is intended to be a drop-in replacement for HDFTrajectoryConfigurator,
    even though it is NOT file-based.
    
**MDTrajTimeStepConfigurator**
------------------------------

  default=0.0

    None

**MDTrajTopologyFileConfigurator**
----------------------------------

  default=

    None

**MDTrajTrajectoryFileConfigurator**
------------------------------------

  default=

    None

    
**MultiInputFileConfigurator**
------------------------------

  default=

    None

**OptionalXYZFileConfigurator**
-------------------------------

  default=

    None


**OutputTrajectoryConfigurator**
--------------------------------

  default=('OUTPUT_TRAJECTORY', 64, 128, 'none', 'no logs')

    
    This configurator allows to define the output directory, the basename, and the format(s) of the output file(s)
    resulting from a trajectory conversion.

    Once configured, this configurator will provide a list of files built by joining the given output directory,
    the basename and the  extensions corresponding to the input file formats.

    For trajectories, MDANSE supports only the HDF format. To define a new output file format for a trajectory
    conversion, you must inherit from the MDANSE.Framework.Formats.IFormat.IFormat interface.
    

**XDATCARFileConfigurator**
---------------------------

  default=

    None

**XTDFileConfigurator**
-----------------------

  default=

    None

**XYZFileConfigurator**
-----------------------

  default=

    This class loads the contents of an XYZ file,
    which in the case of CP2K may contain either the
    positions of atoms, or velocities. In either case
    there will be 3 components per atom.
