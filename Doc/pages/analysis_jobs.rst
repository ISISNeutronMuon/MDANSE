.. _analysis-list:

List of analysis types
======================


.. _analysis-reference-AngularCorrelation:

AngularCorrelation
~~~~~~~~~~~~~~~~~~

Computes the angular correlation of a vector defined in a molecule.

Vector defined by user, starting at the origin pointing in a particular direction.
Origin and direction can either be an atom or a centre definition
(centre of a group of atoms). For example, the origin could be defined by the
geometric centre of the head group of a surfactant molecule and the direction
simply by the last atom of the tail or chain. The correlation is calculated for
the angle formed by the same vector at different simulation frames.

**Calculation:** \n
angle at time T is calculated as the following: \n
.. math:: \\overrightarrow{vector} =  \\overrightarrow{direction} - \\overrightarrow{origin}
.. math:: \phi(T = T_{1}-T_{0}) = arcos(  \\overrightarrow{vector(T_{1})} . \\overrightarrow{vector(T_{0})} )

**Output:** \n
#. angular_correlation_legendre_1st: :math:`<cos(\phi(T))>`
#. angular_correlation_legendre_2nd: :math:`<\\frac{1}{2}(3cos(\phi(T))^{2}-1)>`

**Usage:** \n
This analysis is used to study molecule's orientation and rotation relaxation.

Inputs:

- trajectory: :ref:`configurator-analysis-HDFTrajectoryConfigurator` default=N/A
- frames: :ref:`configurator-analysis-CorrelationFramesConfigurator` default=N/A
- molecule_name: :ref:`configurator-analysis-MoleculeSelectionConfigurator` default=
- per_axis: :ref:`configurator-analysis-BooleanConfigurator` default=False
- output_files: :ref:`configurator-analysis-OutputFilesConfigurator` default=N/A
- running_mode: :ref:`configurator-analysis-RunningModeConfigurator` default=N/A


.. _analysis-reference-AreaPerMolecule:

AreaPerMolecule
~~~~~~~~~~~~~~~

Computes the area per molecule.

The area per molecule is computed by simply dividing the surface of one of the
simulation box faces (*ab*, *bc* or *ac*) by the number of molecules with a
given name. This property should be a constant unless the simulation performed
was in the NPT ensemble. This analysis is relevant for oriented structures
like lipid membranes.

Inputs:

- trajectory: :ref:`configurator-analysis-HDFTrajectoryConfigurator` default=N/A
- frames: :ref:`configurator-analysis-FramesConfigurator` default=N/A
- axis: :ref:`configurator-analysis-SingleChoiceConfigurator` default=ab
- molecule_name: :ref:`configurator-analysis-MoleculeSelectionConfigurator` default=
- output_files: :ref:`configurator-analysis-OutputFilesConfigurator` default=N/A
- running_mode: :ref:`configurator-analysis-RunningModeConfigurator` default=N/A


.. _analysis-reference-AverageStructure:

AverageStructure
~~~~~~~~~~~~~~~~

Outputs a structure file of the atom positions averaged over time.

This analysis only makes sense for crystalline systems
where atoms remain within a finite distance around their
equilibrium positions.

Please run Mean Square Displacement or Root Mean Square Displacement analysis
on your trajectory to make sure that the atoms remain around their equilibrium
positions. Otherwise the time-averaged atom positions will be meaningless.
If your system consists of a crystalline material with migrating guest atoms,
you can output just the crystalline part using a corresponding atom selection.

Inputs:

- trajectory: :ref:`configurator-analysis-HDFTrajectoryConfigurator` default=N/A
- frames: :ref:`configurator-analysis-FramesConfigurator` default=(0, 1, 1)
- atom_selection: :ref:`configurator-analysis-AtomSelectionConfigurator` default=N/A
- fold: :ref:`configurator-analysis-BooleanConfigurator` default=False
- output_units: :ref:`configurator-analysis-SingleChoiceConfigurator` default=Angstrom
- output_files: :ref:`configurator-analysis-OutputStructureConfigurator` default=N/A


.. _analysis-reference-CenterOfMassesTrajectory:

CenterOfMassesTrajectory
~~~~~~~~~~~~~~~~~~~~~~~~

Outputs a trajectory where molecules have been replaced by artificial particles.

Creates a trajectory from the centre of masses for selected groups of atoms in a
given input trajectory. The resulting trajectory will not include the internal
vibrations of molecules or the rotational modes.

Inputs:

- trajectory: :ref:`configurator-analysis-HDFTrajectoryConfigurator` default=N/A
- frames: :ref:`configurator-analysis-FramesConfigurator` default=(0, 1, 1)
- atom_selection: :ref:`configurator-analysis-AtomSelectionConfigurator` default=N/A
- fold: :ref:`configurator-analysis-BooleanConfigurator` default=False
- grouping_level: :ref:`configurator-analysis-GroupingLevelConfigurator` default=molecule
- output_files: :ref:`configurator-analysis-OutputTrajectoryConfigurator` default=N/A


.. _analysis-reference-CoordinationNumber:

CoordinationNumber
~~~~~~~~~~~~~~~~~~

Calculates the coordination number for pairs of atom types.

The Coordination Number is computed from the pair distribution function.
It describes the total number of neighbours, as a function of distance,
from a central atom, or the centre of a group of atoms.

Please not the the Coordination Number results are not symmetrical.
That is, the number of B atoms around an A atom is not equal to the
number of A atoms around a B atom.

Inputs:

- trajectory: :ref:`configurator-analysis-HDFTrajectoryConfigurator` default=N/A
- frames: :ref:`configurator-analysis-FramesConfigurator` default=N/A
- r_values: :ref:`configurator-analysis-DistHistCutoffConfigurator` default=N/A
- grouping_level: :ref:`configurator-analysis-GroupingLevelConfigurator` default=N/A
- atom_selection: :ref:`configurator-analysis-AtomSelectionConfigurator` default=N/A
- atom_transmutation: :ref:`configurator-analysis-AtomTransmutationConfigurator` default=N/A
- output_files: :ref:`configurator-analysis-OutputFilesConfigurator` default=N/A
- running_mode: :ref:`configurator-analysis-RunningModeConfigurator` default=N/A


.. _analysis-reference-CurrentCorrelationFunction:

CurrentCorrelationFunction
~~~~~~~~~~~~~~~~~~~~~~~~~~

Computes the current correlation function for a set of atoms.

The transverse and longitudinal current correlation functions are
typically used to study the propagation of excitations in disordered
systems. The longitudinal current is directly related to density
fluctuations and the transverse current is linked to propagating
'shear modes'.

For more information, see e.g. 'J. P. Hansen and I. R. McDonald,
Theory of Simple Liquids (3rd ed., Elsevier), chapter 7.4:
Correlations in space and time.'

Inputs:

- trajectory: :ref:`configurator-analysis-HDFTrajectoryConfigurator` default=N/A
- frames: :ref:`configurator-analysis-CorrelationFramesConfigurator` default=N/A
- instrument_resolution: :ref:`configurator-analysis-InstrumentResolutionConfigurator` default=N/A
- interpolation_order: :ref:`configurator-analysis-InterpolationOrderConfigurator` default=N/A
- q_vectors: :ref:`configurator-analysis-QVectorsConfigurator` default=N/A
- grouping_level: :ref:`configurator-analysis-GroupingLevelConfigurator` default=N/A
- atom_selection: :ref:`configurator-analysis-AtomSelectionConfigurator` default=N/A
- atom_transmutation: :ref:`configurator-analysis-AtomTransmutationConfigurator` default=N/A
- weights: :ref:`configurator-analysis-WeightsConfigurator` default=equal
- output_files: :ref:`configurator-analysis-OutputFilesConfigurator` default=N/A
- running_mode: :ref:`configurator-analysis-RunningModeConfigurator` default=N/A


.. _analysis-reference-Density:

Density
~~~~~~~

Computes the atom and mass densities for a given trajectory.

These are time dependent if the simulation box volume fluctuates.

Inputs:

- trajectory: :ref:`configurator-analysis-HDFTrajectoryConfigurator` default=N/A
- frames: :ref:`configurator-analysis-FramesConfigurator` default=N/A
- output_files: :ref:`configurator-analysis-OutputFilesConfigurator` default=N/A
- running_mode: :ref:`configurator-analysis-RunningModeConfigurator` default=N/A


.. _analysis-reference-DensityOfStates:

DensityOfStates
~~~~~~~~~~~~~~~

Calculate the vibrational density of states of the trajectory.

The Density Of States describes the number of vibrations per unit frequency.
In MDANSE the DOS calculation returns the Fourier transform (FT) of the weighted
Velocity AutoCorrelation Function (VACF). With an atomic mass weighting scheme
the MDANSE DOS result is proportional to the actual vibrational DOS.
The partial DOS corresponds to selected sets of atoms or molecules.

Inputs:

- trajectory: :ref:`configurator-analysis-HDFTrajectoryConfigurator` default=N/A
- frames: :ref:`configurator-analysis-CorrelationFramesConfigurator` default=N/A
- instrument_resolution: :ref:`configurator-analysis-InstrumentResolutionConfigurator` default=N/A
- interpolation_order: :ref:`configurator-analysis-InterpolationOrderConfigurator` default=N/A
- projection: :ref:`configurator-analysis-ProjectionConfigurator` default=N/A
- grouping_level: :ref:`configurator-analysis-GroupingLevelConfigurator` default=N/A
- atom_selection: :ref:`configurator-analysis-AtomSelectionConfigurator` default=N/A
- atom_transmutation: :ref:`configurator-analysis-AtomTransmutationConfigurator` default=N/A
- weights: :ref:`configurator-analysis-WeightsConfigurator` default=atomic_weight
- output_files: :ref:`configurator-analysis-OutputFilesConfigurator` default=N/A
- running_mode: :ref:`configurator-analysis-RunningModeConfigurator` default=N/A


.. _analysis-reference-DipoleAutoCorrelationFunction:

DipoleAutoCorrelationFunction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Calculates the Dipole Autocorrelation Function of a system.

Partial charges need to be defined in the system for this analysis
to produce non-zero results.

Inputs:

- trajectory: :ref:`configurator-analysis-HDFTrajectoryConfigurator` default=N/A
- frames: :ref:`configurator-analysis-CorrelationFramesConfigurator` default=N/A
- molecule_name: :ref:`configurator-analysis-MoleculeSelectionConfigurator` default=
- atom_charges: :ref:`configurator-analysis-PartialChargeConfigurator` default={}
- output_files: :ref:`configurator-analysis-OutputFilesConfigurator` default=N/A
- running_mode: :ref:`configurator-analysis-RunningModeConfigurator` default=N/A


.. _analysis-reference-DynamicCoherentStructureFactor:

DynamicCoherentStructureFactor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Computes the dynamic coherent structure factor :math:`S_{\text{coh}}(\mathbf{q}, \omega)` for a set of atoms.

It can be compared to experimental data e.g. the energy-integrated, static structure
factor :math:`S_{\text{coh}}(q)` or the dispersion and intensity of phonons.

The coherent part is derived from correlations between pairs of atoms.
This analysis requires the :math:`\mathbf{q}`-vectors to be commensurate
with the reciprocal lattice of the simulation box.

Inputs:

- trajectory: :ref:`configurator-analysis-HDFTrajectoryConfigurator` default=N/A
- frames: :ref:`configurator-analysis-CorrelationFramesConfigurator` default=N/A
- instrument_resolution: :ref:`configurator-analysis-InstrumentResolutionConfigurator` default=N/A
- q_vectors: :ref:`configurator-analysis-QVectorsConfigurator` default=N/A
- grouping_level: :ref:`configurator-analysis-GroupingLevelConfigurator` default=N/A
- atom_selection: :ref:`configurator-analysis-AtomSelectionConfigurator` default=N/A
- atom_transmutation: :ref:`configurator-analysis-AtomTransmutationConfigurator` default=N/A
- weights: :ref:`configurator-analysis-WeightsConfigurator` default=b_coherent
- output_files: :ref:`configurator-analysis-OutputFilesConfigurator` default=N/A
- running_mode: :ref:`configurator-analysis-RunningModeConfigurator` default=N/A


.. _analysis-reference-DynamicIncoherentStructureFactor:

DynamicIncoherentStructureFactor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Computes the dynamic incoherent structure factor :math:`S_{\text{inc}}(\mathbf{q},\omega)` for a set of atoms.

It can be compared to experimental data e.g. the quasielastic scattering due to
diffusion processes.

This property is derived from the self-correlation of individual atoms over time.
While it does not require the :math:`\mathbf{q}`-vectors to be commensurate with the simulation
box reciprocal lattice, a "lattice" vector generator should be chosen if you
intend to combine the result with the coherent part into the total
dynamic structure factor.

Inputs:

- trajectory: :ref:`configurator-analysis-HDFTrajectoryConfigurator` default=N/A
- frames: :ref:`configurator-analysis-CorrelationFramesConfigurator` default=N/A
- instrument_resolution: :ref:`configurator-analysis-InstrumentResolutionConfigurator` default=N/A
- q_vectors: :ref:`configurator-analysis-QVectorsConfigurator` default=N/A
- projection: :ref:`configurator-analysis-ProjectionConfigurator` default=N/A
- grouping_level: :ref:`configurator-analysis-GroupingLevelConfigurator` default=N/A
- atom_selection: :ref:`configurator-analysis-AtomSelectionConfigurator` default=N/A
- atom_transmutation: :ref:`configurator-analysis-AtomTransmutationConfigurator` default=N/A
- weights: :ref:`configurator-analysis-WeightsConfigurator` default=b_incoherent
- output_files: :ref:`configurator-analysis-OutputFilesConfigurator` default=N/A
- running_mode: :ref:`configurator-analysis-RunningModeConfigurator` default=N/A


.. _analysis-reference-Eccentricity:

Eccentricity
~~~~~~~~~~~~

Computes the eccentricity of a selected set of atoms.

The eccentricity is calculated from the principal moments of
inertia via the equation
:math:`\sqrt{\text{pm3}^{2} - \text{pm1}^{2}} / \text{pm3}`
where :math:`\text{pm1}` and :math:`\text{pm3}`
are the smallest and largest principal moments of inertia
respectively. Therefore, for a spherically symmetric molecule its
eccentricity will be 0 while for an aspherical molecule like CO2 its
eccentricity will be 1. This job follows the equations used in rdkit
which was itself taken from https://doi.org/10.1002/9783527618279.ch37.

Inputs:

- trajectory: :ref:`configurator-analysis-HDFTrajectoryConfigurator` default=N/A
- frames: :ref:`configurator-analysis-FramesConfigurator` default=N/A
- atom_selection: :ref:`configurator-analysis-AtomSelectionConfigurator` default=N/A
- output_files: :ref:`configurator-analysis-OutputFilesConfigurator` default=N/A


.. _analysis-reference-ElasticIncoherentStructureFactor:

ElasticIncoherentStructureFactor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Calculates the Elastic Incoherent Structure Factor of a trajectory.

The Elastic Incoherent Structure Factor (EISF) is defined as the limit of the
incoherent intermediate scattering function for infinite time.

The EISF appears as the incoherent amplitude of the elastic line in the neutron
scattering spectrum. Elastic scattering is only present for systems in which
the atomic motion is confined in space, as in solids. The Q-dependence of the
EISF indicates e.g. the fraction of static/mobile atoms and the spatial dependence
of the dynamics.

Inputs:

- trajectory: :ref:`configurator-analysis-HDFTrajectoryConfigurator` default=N/A
- frames: :ref:`configurator-analysis-FramesConfigurator` default=N/A
- q_vectors: :ref:`configurator-analysis-QVectorsConfigurator` default=N/A
- projection: :ref:`configurator-analysis-ProjectionConfigurator` default=N/A
- grouping_level: :ref:`configurator-analysis-GroupingLevelConfigurator` default=N/A
- atom_selection: :ref:`configurator-analysis-AtomSelectionConfigurator` default=N/A
- atom_transmutation: :ref:`configurator-analysis-AtomTransmutationConfigurator` default=N/A
- weights: :ref:`configurator-analysis-WeightsConfigurator` default=b_incoherent
- output_files: :ref:`configurator-analysis-OutputFilesConfigurator` default=N/A
- running_mode: :ref:`configurator-analysis-RunningModeConfigurator` default=N/A


.. _analysis-reference-GaussianDynamicIncoherentStructureFactor:

GaussianDynamicIncoherentStructureFactor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Computes the dynamic incoherent structure factor in the Gaussian approximation.

Gaussian approximation is exact for a system of free particles and a system of
particles undergoing brownian motion. The results of this analysis will be close
to the Dynamic Incoherent Structure Factor analysis in the limits of very
short :math:`\mathbf{q}` and very long :math:`\mathbf{q}`, and will differ from
it for intermediate :math:`\mathbf{q}` values.

Inputs:

- trajectory: :ref:`configurator-analysis-HDFTrajectoryConfigurator` default=N/A
- frames: :ref:`configurator-analysis-CorrelationFramesConfigurator` default=N/A
- q_shells: :ref:`configurator-analysis-RangeConfigurator` default=N/A
- instrument_resolution: :ref:`configurator-analysis-InstrumentResolutionConfigurator` default=N/A
- projection: :ref:`configurator-analysis-ProjectionConfigurator` default=N/A
- grouping_level: :ref:`configurator-analysis-GroupingLevelConfigurator` default=N/A
- atom_selection: :ref:`configurator-analysis-AtomSelectionConfigurator` default=N/A
- atom_transmutation: :ref:`configurator-analysis-AtomTransmutationConfigurator` default=N/A
- weights: :ref:`configurator-analysis-WeightsConfigurator` default=b_incoherent
- output_files: :ref:`configurator-analysis-OutputFilesConfigurator` default=N/A
- running_mode: :ref:`configurator-analysis-RunningModeConfigurator` default=N/A


.. _analysis-reference-Infrared:

Infrared
~~~~~~~~

Calculates the infrared spectrum of a system of molecules.

The infrared spectrum is calculated as the autocorrelation of the derivative
the molecular dipole moments.

This analysis requires molecules to be defined in the system,
and partial charges to be set to non-zero values.

Inputs:

- trajectory: :ref:`configurator-analysis-HDFTrajectoryConfigurator` default=N/A
- frames: :ref:`configurator-analysis-CorrelationFramesConfigurator` default=N/A
- instrument_resolution: :ref:`configurator-analysis-InstrumentResolutionConfigurator` default=N/A
- derivative_order: :ref:`configurator-analysis-DerivativeOrderConfigurator` default=N/A
- molecule_name: :ref:`configurator-analysis-MoleculeSelectionConfigurator` default=
- atom_charges: :ref:`configurator-analysis-PartialChargeConfigurator` default={}
- output_files: :ref:`configurator-analysis-OutputFilesConfigurator` default=N/A
- running_mode: :ref:`configurator-analysis-RunningModeConfigurator` default=N/A


.. _analysis-reference-MeanSquareDisplacement:

MeanSquareDisplacement
~~~~~~~~~~~~~~~~~~~~~~

Calculates the mean square displacement (MSD) of atoms in the trajectory.

The MSD is a representation of diffusion in the system. The motion of an individual
atom or molecule does not follow a simple path since particles undergo collisions.
The path is to a good approximation to a random walk.

Mathematically, a random walk is a series of steps where each step is taken in a
completely random direction from the one before, as analyzed by Albert Einstein
in a study of Brownian motion. The MSD of a particle in this case
is proportional to the time elapsed:

.. math:: \langle d^{2}(t) \rangle = 6Dt + C

where :math:`\langle d^{2}(t) \rangle` is the MSD and :math:`t` is the time.
:math:`D` and :math:`C` are constants. The constant :math:`D` is the so-called
diffusion coefficient.

More generally the MSD reveals the distance or volume explored by atoms and
molecules as a function of time. In crystals, the MSD quickly saturates at a
constant value which corresponds to the vibrational amplitude.
Diffusion in a volume will also have a limiting value of the MSD which corresponds
to the diameter of the volume and the saturation value is reached more slowly.
The MSD can also reveal e.g. sub-diffusion regimes for the translational
diffusion of lipids in membranes.

Inputs:

- trajectory: :ref:`configurator-analysis-HDFTrajectoryConfigurator` default=N/A
- frames: :ref:`configurator-analysis-CorrelationFramesConfigurator` default=N/A
- projection: :ref:`configurator-analysis-ProjectionConfigurator` default=N/A
- grouping_level: :ref:`configurator-analysis-GroupingLevelConfigurator` default=N/A
- atom_selection: :ref:`configurator-analysis-AtomSelectionConfigurator` default=N/A
- atom_transmutation: :ref:`configurator-analysis-AtomTransmutationConfigurator` default=N/A
- weights: :ref:`configurator-analysis-WeightsConfigurator` default=N/A
- output_files: :ref:`configurator-analysis-OutputFilesConfigurator` default=N/A
- running_mode: :ref:`configurator-analysis-RunningModeConfigurator` default=N/A


.. _analysis-reference-MolecularTrace:

MolecularTrace
~~~~~~~~~~~~~~

Maps the volume occupied by atoms over time.

A Molecular Trace is a time-integrated trace of selected atoms coordinates.

* the minimal and maximal coordinates from the selected atomic trajectories are
computed.
* based on these min/max and a spatial resolution, a cartesian grid is constructed.
* for each atom and for each frame of the selected trajectories, a histogram of
presence, called the spatial density, is constructed.

The molecular trace can reveal anisotropic vibrations and diffusion pathways.

**Acknowledgement and publication:**
Gael Goret, PELLEGRINI Eric

Inputs:

- trajectory: :ref:`configurator-analysis-HDFTrajectoryConfigurator` default=N/A
- frames: :ref:`configurator-analysis-FramesConfigurator` default=N/A
- atom_selection: :ref:`configurator-analysis-AtomSelectionConfigurator` default=N/A
- spatial_resolution: :ref:`configurator-analysis-FloatConfigurator` default=0.1
- output_files: :ref:`configurator-analysis-OutputFilesConfigurator` default=N/A
- running_mode: :ref:`configurator-analysis-RunningModeConfigurator` default=N/A


.. _analysis-reference-NeutronDynamicTotalStructureFactor:

NeutronDynamicTotalStructureFactor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Combines the coherent and incoherent dynamic structure factors.

The partial results need to be calculated before using the Dynamic
Coherent/Incoherent Structure Factor jobs with the same
:math:`\mathbf{q}`-vector settings.

The partial results will be scaled by neutron scattering lengths, producing
a total result with coherent and incoherent parts on the same scale,
directly comparable to each other.

Inputs:

- trajectory: :ref:`configurator-analysis-HDFTrajectoryConfigurator` default=N/A
- dcsf_input_file: :ref:`configurator-analysis-HDFInputFileConfigurator` default=dcsf.mda
- disf_input_file: :ref:`configurator-analysis-HDFInputFileConfigurator` default=disf.mda
- grouping_level: :ref:`configurator-analysis-GroupingLevelConfigurator` default=N/A
- atom_selection: :ref:`configurator-analysis-AtomSelectionConfigurator` default=N/A
- atom_transmutation: :ref:`configurator-analysis-AtomTransmutationConfigurator` default=N/A
- output_files: :ref:`configurator-analysis-OutputFilesConfigurator` default=N/A


.. _analysis-reference-PairDistributionFunction:

PairDistributionFunction
~~~~~~~~~~~~~~~~~~~~~~~~

Calculates a histogram of interatomic distances.

The Pair-Distribution Function (PDF) is an example of a pair correlation function,
which describes how, on average, the atoms in a system are radially packed around
each other. This is a particularly effective way of describing the average
structure of disordered molecular systems such as liquids. Also in systems like
liquids, where there is continual movement of the atoms and a single snapshot of
the system shows only the instantaneous disorder, it is essential to determine
the average structure.

The PDF can be compared with experimental data from x-ray or neutron diffraction.
It can be used in conjunction with the inter-atomic pair potential
function to calculate the internal energy of the system, usually quite accurately.
Finally it can even be used to derive the inter-atomic potentials of mean force.

Inputs:

- trajectory: :ref:`configurator-analysis-HDFTrajectoryConfigurator` default=N/A
- frames: :ref:`configurator-analysis-FramesConfigurator` default=N/A
- r_values: :ref:`configurator-analysis-DistHistCutoffConfigurator` default=N/A
- grouping_level: :ref:`configurator-analysis-GroupingLevelConfigurator` default=N/A
- atom_selection: :ref:`configurator-analysis-AtomSelectionConfigurator` default=N/A
- atom_transmutation: :ref:`configurator-analysis-AtomTransmutationConfigurator` default=N/A
- weights: :ref:`configurator-analysis-WeightsConfigurator` default=N/A
- output_files: :ref:`configurator-analysis-OutputFilesConfigurator` default=N/A
- running_mode: :ref:`configurator-analysis-RunningModeConfigurator` default=N/A


.. _analysis-reference-PositionAutoCorrelationFunction:

PositionAutoCorrelationFunction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Calculates the position autocorrelation function.

Like the velocity autocorrelation function, but using positions instead of
velocities.

Inputs:

- trajectory: :ref:`configurator-analysis-HDFTrajectoryConfigurator` default=N/A
- frames: :ref:`configurator-analysis-CorrelationFramesConfigurator` default=N/A
- projection: :ref:`configurator-analysis-ProjectionConfigurator` default=N/A
- grouping_level: :ref:`configurator-analysis-GroupingLevelConfigurator` default=N/A
- atom_selection: :ref:`configurator-analysis-AtomSelectionConfigurator` default=N/A
- atom_transmutation: :ref:`configurator-analysis-AtomTransmutationConfigurator` default=N/A
- weights: :ref:`configurator-analysis-WeightsConfigurator` default=N/A
- output_files: :ref:`configurator-analysis-OutputFilesConfigurator` default=N/A
- running_mode: :ref:`configurator-analysis-RunningModeConfigurator` default=N/A


.. _analysis-reference-PositionPowerSpectrum:

PositionPowerSpectrum
~~~~~~~~~~~~~~~~~~~~~

Calculates the position power spectrum.

Power spectrum (using Fast Fourier Transform) of atomic trajectories calculated
from the Positional Autocorrelation Function (PACF). The calculation result
is similar to the density of states, which is calculated from the velocity
autocorrelation function. In fact, PPS and DOS may show the same features
in systems where position and velocity are strongly correlated (i.e. solids).

This calculation is used by TrajectoryFilter to create a preview of the spectrum,
so that a desired range of atomic vibrational modes can be isolated.

Inputs:

- trajectory: :ref:`configurator-analysis-HDFTrajectoryConfigurator` default=N/A
- frames: :ref:`configurator-analysis-CorrelationFramesConfigurator` default=N/A
- instrument_resolution: :ref:`configurator-analysis-InstrumentResolutionConfigurator` default=N/A
- projection: :ref:`configurator-analysis-ProjectionConfigurator` default=N/A
- grouping_level: :ref:`configurator-analysis-GroupingLevelConfigurator` default=N/A
- atom_selection: :ref:`configurator-analysis-AtomSelectionConfigurator` default=N/A
- atom_transmutation: :ref:`configurator-analysis-AtomTransmutationConfigurator` default=N/A
- weights: :ref:`configurator-analysis-WeightsConfigurator` default=atomic_weight
- output_files: :ref:`configurator-analysis-OutputFilesConfigurator` default=N/A
- running_mode: :ref:`configurator-analysis-RunningModeConfigurator` default=N/A


.. _analysis-reference-RadiusOfGyration:

RadiusOfGyration
~~~~~~~~~~~~~~~~

Calculates the radius of gyration of selected atoms.

The Radius of Gyration can be used, for example, to determine the
compactness of a molecule. It is calculated as a root (mass weighted)
mean square distance of the atoms of a molecule relative to its
centre of mass. ROG can be used to follow the size and spread of
a molecule during the molecular dynamics simulation.

Inputs:

- trajectory: :ref:`configurator-analysis-HDFTrajectoryConfigurator` default=N/A
- frames: :ref:`configurator-analysis-FramesConfigurator` default=N/A
- atom_selection: :ref:`configurator-analysis-AtomSelectionConfigurator` default=N/A
- output_files: :ref:`configurator-analysis-OutputFilesConfigurator` default=N/A
- running_mode: :ref:`configurator-analysis-RunningModeConfigurator` default=N/A


.. _analysis-reference-RootMeanSquareDeviation:

RootMeanSquareDeviation
~~~~~~~~~~~~~~~~~~~~~~~

Calculates the Root Mean Square Deviation of the selected atoms.

The Root Mean-Square Deviation (RMSD) is one of the most popular measures
of structural similarity. It is a numerical measure of the difference
between two structures. Typically, the RMSD is used to quantify the structural
evolution of the system during the simulation. It can provide essential
information about the structure, if it reached equilibrium or conversely
if major structural changes occurred during the simulation.

Inputs:

- trajectory: :ref:`configurator-analysis-HDFTrajectoryConfigurator` default=N/A
- frames: :ref:`configurator-analysis-FramesConfigurator` default=N/A
- reference_frame: :ref:`configurator-analysis-IntegerConfigurator` default=0
- grouping_level: :ref:`configurator-analysis-GroupingLevelConfigurator` default=N/A
- atom_selection: :ref:`configurator-analysis-AtomSelectionConfigurator` default=N/A
- atom_transmutation: :ref:`configurator-analysis-AtomTransmutationConfigurator` default=N/A
- output_files: :ref:`configurator-analysis-OutputFilesConfigurator` default=N/A
- running_mode: :ref:`configurator-analysis-RunningModeConfigurator` default=N/A


.. _analysis-reference-RootMeanSquareFluctuation:

RootMeanSquareFluctuation
~~~~~~~~~~~~~~~~~~~~~~~~~

Calculates the Root Mean Square Fluctuation of atom positions.

The root mean square fluctuation (RMSF) for a set of atoms is similar to the
square root of the mean square displacement (MSD), except that it is spatially
resolved (by atom/residue/etc) rather than time resolved. It reveals the
dynamical heterogeneity of the molecule over the course of a MD simulation.

As opposed to most analysis types, the result is a single number per atom index.

Inputs:

- trajectory: :ref:`configurator-analysis-HDFTrajectoryConfigurator` default=N/A
- frames: :ref:`configurator-analysis-FramesConfigurator` default=N/A
- grouping_level: :ref:`configurator-analysis-GroupingLevelConfigurator` default=each atom
- atom_selection: :ref:`configurator-analysis-AtomSelectionConfigurator` default=N/A
- output_files: :ref:`configurator-analysis-OutputFilesConfigurator` default=N/A
- running_mode: :ref:`configurator-analysis-RunningModeConfigurator` default=N/A


.. _analysis-reference-ScatteringLengthDensityProfile:

ScatteringLengthDensityProfile
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Produces the time-averaged scattering length density profile.

The main result, named 'sldp' in the output file, is the time-averaged
coherent scattering length density profile in units of 10^-6 / Ang^2,
as used in neutron reflectometry calculations.

You may want to export the 'sldp' dataset as text file using the MDANSE_GUI
plotter, and load it into your preferred neutron reflectometry software.

Additionally, the following other profiles are provided in the output:

- 'sldp_incoherent', the incoherent scattering length profile,
- 'sldp_total', the total scattering length profile,
- 'dp_{atom_type}', numeric density profiles (number of atoms per volume)


Inputs:

- trajectory: :ref:`configurator-analysis-HDFTrajectoryConfigurator` default=N/A
- frames: :ref:`configurator-analysis-FramesConfigurator` default=N/A
- atom_selection: :ref:`configurator-analysis-AtomSelectionConfigurator` default=N/A
- atom_transmutation: :ref:`configurator-analysis-AtomTransmutationConfigurator` default=N/A
- axis: :ref:`configurator-analysis-SingleChoiceConfigurator` default=c
- dr: :ref:`configurator-analysis-FloatConfigurator` default=0.01
- output_files: :ref:`configurator-analysis-OutputFilesConfigurator` default=N/A
- running_mode: :ref:`configurator-analysis-RunningModeConfigurator` default=N/A


.. _analysis-reference-SolventAccessibleSurface:

SolventAccessibleSurface
~~~~~~~~~~~~~~~~~~~~~~~~

Calculates the accessible surface of the selected atoms.

Please keep in mind that the atoms outside of the selection are still considered to
be blocking the accessible surface. If you are interested in the **total** surface
of a group of atoms, please remove the other atoms from the trajectory.

Solvent Accessible Surface is calculated using the 'rolling ball' algorithm
developed by Shrake & Rupley in 1973.

* Shrake, A., and J. A. Rupley. JMB (1973) 79:351-371.

This algorithm uses a sphere (of solvent) of a particular radius to 'probe' the
surface of the molecule.

It involves constructing a mesh of points equidistant from each atom of the molecule
and uses the number of these points that are solvent accessible to determine the
surface area. The points are drawn at a water molecule's estimated radius beyond
the van der Waals radius, which is effectively similar to 'rolling a ball' along
the surface. All points are checked against the surface of neighboring atoms
to determine whether they are buried or accessible. The number of points
accessible is multiplied by the portion of surface area each point represents
to calculate the SAS.

The choice of the 'probe radius' has an effect on the observed surface area -
using a smaller probe radius detects more surface details and therefore reports
a larger surface. A typical value is 0.14 nm, which is approximately the radius
of a water molecule. Another factor that affects the result is the definition
of the VDW radii of the atoms in the molecule under study.

Inputs:

- trajectory: :ref:`configurator-analysis-HDFTrajectoryConfigurator` default=N/A
- frames: :ref:`configurator-analysis-FramesConfigurator` default=(0, 2, 1)
- atom_selection: :ref:`configurator-analysis-AtomSelectionConfigurator` default=N/A
- n_sphere_points: :ref:`configurator-analysis-IntegerConfigurator` default=1000
- probe_radius: :ref:`configurator-analysis-FloatConfigurator` default=0.14
- output_files: :ref:`configurator-analysis-OutputFilesConfigurator` default=N/A
- running_mode: :ref:`configurator-analysis-RunningModeConfigurator` default=N/A


.. _analysis-reference-StaticStructureFactor:

StaticStructureFactor
~~~~~~~~~~~~~~~~~~~~~

Computes the static structure factor for a set of atoms.

The static structure factor is calculated as a Fourier transform of the partial pair
distribution function (following the Faber-Ziman definition).

Inputs:

- trajectory: :ref:`configurator-analysis-HDFTrajectoryConfigurator` default=N/A
- frames: :ref:`configurator-analysis-FramesConfigurator` default=N/A
- r_values: :ref:`configurator-analysis-DistHistCutoffConfigurator` default=N/A
- q_values: :ref:`configurator-analysis-RangeConfigurator` default=(0, 500, 1)
- grouping_level: :ref:`configurator-analysis-GroupingLevelConfigurator` default=N/A
- atom_selection: :ref:`configurator-analysis-AtomSelectionConfigurator` default=N/A
- atom_transmutation: :ref:`configurator-analysis-AtomTransmutationConfigurator` default=N/A
- weights: :ref:`configurator-analysis-WeightsConfigurator` default=b_coherent
- output_files: :ref:`configurator-analysis-OutputFilesConfigurator` default=N/A
- running_mode: :ref:`configurator-analysis-RunningModeConfigurator` default=N/A


.. _analysis-reference-StructureFactorFromScatteringFunction:

StructureFactorFromScatteringFunction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Computes the static structure factor from the results of another analysis.

The static structure factor is calculated from the intermediate
scattering function of the dynamic coherent scattering function
calculation results.

Inputs:

- trajectory: :ref:`configurator-analysis-HDFTrajectoryConfigurator` default=N/A
- dcsf_input_file: :ref:`configurator-analysis-HDFInputFileConfigurator` default=dcsf.mda
- grouping_level: :ref:`configurator-analysis-GroupingLevelConfigurator` default=N/A
- atom_selection: :ref:`configurator-analysis-AtomSelectionConfigurator` default=N/A
- atom_transmutation: :ref:`configurator-analysis-AtomTransmutationConfigurator` default=N/A
- output_files: :ref:`configurator-analysis-OutputFilesConfigurator` default=N/A


.. _analysis-reference-Temperature:

Temperature
~~~~~~~~~~~

Calculates the temperature of the system for every selected frame.

Computes the time-dependent temperature for a given trajectory.
The temperature is determined from the kinetic energy i.e. the atomic velocities
which are in turn calculated from the time-dependence of the atomic coordinates.

Note that the velocity calculated from atom positions will be underestimated
and the error in the results will be larger for trajectories with
a large step between (saved) frames compared to the actual time step of the
MD simulations (~fs).

Inputs:

- trajectory: :ref:`configurator-analysis-HDFTrajectoryConfigurator` default=N/A
- frames: :ref:`configurator-analysis-FramesConfigurator` default=N/A
- interpolation_order: :ref:`configurator-analysis-InterpolationOrderConfigurator` default=N/A
- output_files: :ref:`configurator-analysis-OutputFilesConfigurator` default=N/A
- running_mode: :ref:`configurator-analysis-RunningModeConfigurator` default=N/A


.. _analysis-reference-TrajectoryEditor:

TrajectoryEditor
~~~~~~~~~~~~~~~~

Write out a modified version of the input trajectory.

At the moment, the main applications include:

- molecule detection,
- setting unit cell parameters,
- setting partial charges,
- removing or transmuting atoms,
- removing frames.

Inputs:

- trajectory: :ref:`configurator-analysis-HDFTrajectoryConfigurator` default=N/A
- frames: :ref:`configurator-analysis-FramesConfigurator` default=(0, -1, 1)
- unit_cell: :ref:`configurator-analysis-UnitCellConfigurator` default=(array([[1., 0., 0.],
       [0., 1., 0.],
       [0., 0., 1.]]), False)
- atom_selection: :ref:`configurator-analysis-AtomSelectionConfigurator` default=N/A
- atom_transmutation: :ref:`configurator-analysis-AtomTransmutationConfigurator` default=N/A
- atom_charges: :ref:`configurator-analysis-PartialChargeConfigurator` default={}
- molecule_tolerance: :ref:`configurator-analysis-OptionalFloatConfigurator` default=[False, 0.04]
- output_files: :ref:`configurator-analysis-OutputTrajectoryConfigurator` default=N/A


.. _analysis-reference-TrajectoryFilter:

TrajectoryFilter
~~~~~~~~~~~~~~~~

Design and apply a filter for the atomic trajectories.

This job outputs a new trajectory, where part of the vibrational
spectrum of atoms has been removed. Effectively, this allows to
separate the high- and low-frequency vibrational modes, also in
disordered systems where lattice-dynamics analysis would be difficult.

The filter is applied in the standard signal-processing approach,
where the positions of atoms as a function of time are Fourier-transformed
(producing a position power spectrum), the filter is applied to the spectrum,
and the modified spectrum is Fourier-transformed back into positions.

Inputs:

- trajectory: :ref:`configurator-analysis-HDFTrajectoryConfigurator` default=N/A
- frames: :ref:`configurator-analysis-CorrelationFramesConfigurator` default=N/A
- instrument_resolution: :ref:`configurator-analysis-InstrumentResolutionConfigurator` default=N/A
- projection: :ref:`configurator-analysis-ProjectionConfigurator` default=N/A
- trajectory_filter: :ref:`configurator-analysis-TrajectoryFilterConfigurator` default=N/A
- atom_selection: :ref:`configurator-analysis-AtomSelectionConfigurator` default=N/A
- weights: :ref:`configurator-analysis-WeightsConfigurator` default=atomic_weight
- output_files: :ref:`configurator-analysis-OutputTrajectoryConfigurator` default=N/A
- running_mode: :ref:`configurator-analysis-RunningModeConfigurator` default=N/A


.. _analysis-reference-VanHoveFunctionDistinct:

VanHoveFunctionDistinct
~~~~~~~~~~~~~~~~~~~~~~~

Calculates the distinct van Hove function.

The van Hove function is related to the intermediate scattering
function via a Fourier transform and the dynamic structure factor
via a double Fourier transform. The van Hove function describes the
probability of finding a particle (j) at a distance r at time t from
a particle (i) at a time t_0. The van Hove function can be split
into self and distinct parts. The self part includes only the
contributions from only the same particles (i=j) while the distinct
part includes only the contributions between different particles
(i≠j). This job calculates a distinct part of the van Hove function,
spherically averaged and normalised so that G(r,t)=1 as r→∞ or t→∞
for liquid or gaseous systems and G(r,0)=PDF(r).

Inputs:

- trajectory: :ref:`configurator-analysis-HDFTrajectoryConfigurator` default=N/A
- frames: :ref:`configurator-analysis-CorrelationFramesConfigurator` default=N/A
- r_values: :ref:`configurator-analysis-DistHistCutoffConfigurator` default=N/A
- grouping_level: :ref:`configurator-analysis-GroupingLevelConfigurator` default=N/A
- atom_selection: :ref:`configurator-analysis-AtomSelectionConfigurator` default=N/A
- atom_transmutation: :ref:`configurator-analysis-AtomTransmutationConfigurator` default=N/A
- weights: :ref:`configurator-analysis-WeightsConfigurator` default=N/A
- output_files: :ref:`configurator-analysis-OutputFilesConfigurator` default=N/A
- running_mode: :ref:`configurator-analysis-RunningModeConfigurator` default=N/A


.. _analysis-reference-VanHoveFunctionSelf:

VanHoveFunctionSelf
~~~~~~~~~~~~~~~~~~~

Calculates the self part of the van Hove function.

The van Hove function is related to the intermediate scattering
function via a Fourier transform and the dynamic structure factor
via a double Fourier transform. The van Hove function describes the
probability of finding a particle (j) at a distance r at time t from
a particle (i) at a time t_0. The van Hove function can be split
into self and distinct parts. The self part includes only the
contributions from only the same particles (i=j) while the distinct
part includes only the contributions between different particles
(i≠j). This job calculates a self part of the van Hove function.

Inputs:

- trajectory: :ref:`configurator-analysis-HDFTrajectoryConfigurator` default=N/A
- frames: :ref:`configurator-analysis-CorrelationFramesConfigurator` default=N/A
- r_values: :ref:`configurator-analysis-DistHistCutoffConfigurator` default=N/A
- grouping_level: :ref:`configurator-analysis-GroupingLevelConfigurator` default=N/A
- atom_selection: :ref:`configurator-analysis-AtomSelectionConfigurator` default=N/A
- atom_transmutation: :ref:`configurator-analysis-AtomTransmutationConfigurator` default=N/A
- weights: :ref:`configurator-analysis-WeightsConfigurator` default=N/A
- output_files: :ref:`configurator-analysis-OutputFilesConfigurator` default=N/A
- running_mode: :ref:`configurator-analysis-RunningModeConfigurator` default=N/A


.. _analysis-reference-VelocityAutoCorrelationFunction:

VelocityAutoCorrelationFunction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Calculates the velocity autocorrelation function of the selected atoms.

The Velocity AutoCorrelation Function (VACF) is a property describing the dynamics
of a molecular system. It reveals the underlying nature of the forces acting on
the system. Its Fourier Transform gives the cartesian density of states for a set
of atoms.

Inputs:

- trajectory: :ref:`configurator-analysis-HDFTrajectoryConfigurator` default=N/A
- frames: :ref:`configurator-analysis-CorrelationFramesConfigurator` default=N/A
- interpolation_order: :ref:`configurator-analysis-InterpolationOrderConfigurator` default=N/A
- projection: :ref:`configurator-analysis-ProjectionConfigurator` default=N/A
- grouping_level: :ref:`configurator-analysis-GroupingLevelConfigurator` default=N/A
- atom_selection: :ref:`configurator-analysis-AtomSelectionConfigurator` default=N/A
- atom_transmutation: :ref:`configurator-analysis-AtomTransmutationConfigurator` default=N/A
- weights: :ref:`configurator-analysis-WeightsConfigurator` default=N/A
- output_files: :ref:`configurator-analysis-OutputFilesConfigurator` default=N/A
- running_mode: :ref:`configurator-analysis-RunningModeConfigurator` default=N/A


.. _analysis-reference-Voronoi:

Voronoi
~~~~~~~

Performs the Voronoi analysis of available volume per atom.

Computes the volume of each Voronoi cell and corresponding 'neighbourhood'
statistics for 3d systems. Vornoi diagram and Delaunay tesselation are
used as implemented in scipy.spatial module. Replicas of atoms from
the simulation box will be included in the calculation within
a finite distance from the box wall (given in nm).

Voronoi analysis is another commonly-used, complementary method for
characterising the local structure of a system.

**Acknowledgement:**
Gael Goret, PELLEGRINI Eric


Inputs:

- trajectory: :ref:`configurator-analysis-HDFTrajectoryConfigurator` default=N/A
- frames: :ref:`configurator-analysis-FramesConfigurator` default=(0, 5, 1)
- pbc: :ref:`configurator-analysis-BooleanConfigurator` default=True
- pbc_border_size: :ref:`configurator-analysis-FloatConfigurator` default=0.2
- output_files: :ref:`configurator-analysis-OutputFilesConfigurator` default=N/A


.. _analysis-reference-XRayStaticStructureFactor:

XRayStaticStructureFactor
~~~~~~~~~~~~~~~~~~~~~~~~~

Computes the X-ray static structure for a set of atoms.

Computes the X-ray static structure from the pair distribution function for a
set of atoms, taking into account the atomic form factor for X-rays.

Inputs:

- trajectory: :ref:`configurator-analysis-HDFTrajectoryConfigurator` default=N/A
- frames: :ref:`configurator-analysis-FramesConfigurator` default=N/A
- r_values: :ref:`configurator-analysis-DistHistCutoffConfigurator` default=N/A
- q_values: :ref:`configurator-analysis-RangeConfigurator` default=(0, 500, 1)
- grouping_level: :ref:`configurator-analysis-GroupingLevelConfigurator` default=N/A
- atom_selection: :ref:`configurator-analysis-AtomSelectionConfigurator` default=N/A
- atom_transmutation: :ref:`configurator-analysis-AtomTransmutationConfigurator` default=N/A
- output_files: :ref:`configurator-analysis-OutputFilesConfigurator` default=N/A
- running_mode: :ref:`configurator-analysis-RunningModeConfigurator` default=N/A

